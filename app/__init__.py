import os
import logging
import datetime
from flask import Flask, jsonify, render_template, request, g, current_app, session
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import generate_csrf, CSRFProtect
from app.config.config import Config, TestingConfig, ProductionConfig
from app.config.logging_config import setup_logging
from app.auth.firebase import init_firebase
from app.extensions import db, migrate, cors, login_manager, jwt, csrf, Base, limiter, talisman, configure_cache
from app.auth.routes import auth_bp
from app.routes import blueprints  # Import the list of blueprints
from app.models.user import User
from app.models.contact import Contact
from app.models.person import Person
from app.models.church import Church
from app.models.office import Office
from app.models.task import Task
from app.models.communication import Communication
from app.models.relationships import setup_relationships
from app.tasks.scheduler import init_scheduler
from app.utils.filters import register_filters, register_template_functions
from app.utils.firebase import firebase_setup
from app.utils.context_processors import register_template_utilities
from app.utils.setup_main_pipelines import setup_main_pipelines
from app.utils.migrate_contacts_to_main_pipeline import migrate_contacts_to_main_pipeline
from app.utils.ensure_church_pipeline import init_app as init_church_pipeline
from app.cli import register_commands

# Function to access secrets from Secret Manager in production
def access_secrets():
    """Access secrets from Google Cloud Secret Manager when in production"""
    secrets = {}
    
    if os.environ.get('FLASK_ENV') == 'production':
        try:
            from google.cloud import secretmanager
            
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'mobilize-crm')
            client = secretmanager.SecretManagerServiceClient()
            
            # Function to access a specific secret
            def access_secret(secret_id):
                name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
                response = client.access_secret_version(request={"name": name})
                return response.payload.data.decode('UTF-8')
            
            # Access required secrets
            db_url = access_secret('mobilize-db-url')
            
            # Fix potential formatting issues with the database URL
            if db_url and not db_url.startswith('postgresql://'):
                if db_url.startswith('postgresql:'):
                    # Add missing // and ensure username is included
                    db_url = db_url.replace('postgresql:', 'postgresql://postgres.fwnitauuyzxnsvgsbrzr:')
                    
            secrets = {
                'DATABASE_URL': db_url,
                'SECRET_KEY': access_secret('mobilize-flask-secret'),
                'GOOGLE_CLIENT_ID': access_secret('mobilize-google-client-id'),
                'GOOGLE_CLIENT_SECRET': access_secret('mobilize-google-client-secret')
            }
            logging.info("Successfully loaded secrets from Secret Manager")
        except Exception as e:
            logging.error(f"Error accessing secrets from Secret Manager: {e}")
    
    return secrets

# Initialize extensions that aren't in extensions.py
# (Remove this as we're using the ones from extensions.py)

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Add a simple health check endpoint that doesn't rely on database
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'message': 'Basic health check passed'
        }), 200
    
    # Add another health check that includes more details
    @app.route('/api/health-check', methods=['GET'])
    def api_health_check():
        status = {
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'database': 'unknown',
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }
        
        # Try to check database connection but don't fail if it doesn't work
        try:
            with app.app_context():
                from sqlalchemy import text
                db_result = db.session.execute(text('SELECT 1')).fetchone()
                status['database'] = 'connected' if db_result else 'error'
        except Exception as e:
            app.logger.error(f"Database health check failed: {str(e)}")
            status['database'] = 'error'
            status['database_error'] = str(e)
        
        return jsonify(status)
    
    # Add an endpoint to debug the connection string
    @app.route('/api/debug/db-config', methods=['GET'])
    def debug_db_config():
        # Return masked connection string info for debugging
        db_url = os.environ.get('DATABASE_URL', 'not-set')
        db_conn = os.environ.get('DB_CONNECTION_STRING', 'not-set')
        
        # Mask passwords in output
        def mask_password(url):
            if not url or url == 'not-set':
                return url
                
            if '@' in url and ':' in url.split('@')[0]:
                parts = url.split('@')
                user_parts = parts[0].split(':')
                return f"{user_parts[0]}:******@{parts[1]}"
            return url
        
        # Check if the secret was loaded correctly
        secret_db_url = 'not-loaded'
        try:
            if os.environ.get('FLASK_ENV') == 'production':
                from google.cloud import secretmanager
                project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'mobilize-crm')
                client = secretmanager.SecretManagerServiceClient()
                name = f"projects/{project_id}/secrets/mobilize-db-url/versions/latest"
                response = client.access_secret_version(request={"name": name})
                secret_db_url = response.payload.data.decode('UTF-8')
                # Mask password for security
                secret_db_url = mask_password(secret_db_url)
        except Exception as e:
            secret_db_url = f"Error: {str(e)}"
        
        # Get the actual connection string from app config
        config_db_url = mask_password(app.config.get('SQLALCHEMY_DATABASE_URI', 'not-set-in-config'))
        
        return jsonify({
            'env': os.environ.get('FLASK_ENV', 'unknown'),
            'database_url_masked': mask_password(db_url),
            'db_conn_string_masked': mask_password(db_conn),
            'secret_manager_url_masked': secret_db_url,
            'config_db_url_masked': config_db_url,
            'using_secret_manager': os.environ.get('FLASK_ENV') == 'production'
        })
    
    # Load secrets from Secret Manager in production
    secrets = access_secrets()
    
    # DEBUGGING: Temporarily prioritize environment variables
    env_db_url = os.environ.get('DATABASE_URL')
    env_db_conn = os.environ.get('DB_CONNECTION_STRING')
    
    # Log which source is being used
    if env_db_url:
        app.logger.info("Using DATABASE_URL from environment variables")
    elif secrets.get('DATABASE_URL'):
        app.logger.info("Using DATABASE_URL from Secret Manager")
    else:
        app.logger.warning("No DATABASE_URL found in environment or Secret Manager!")
    
    app.config.from_mapping(
        SECRET_KEY=secrets.get('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev')),
        DEBUG=os.environ.get('FLASK_DEBUG', 'False') == 'True',
        # Database Configuration - REVERSED PRIORITY FOR DEBUGGING
        SQLALCHEMY_DATABASE_URI=env_db_url or env_db_conn or secrets.get('DATABASE_URL', ''),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Cache Configuration for session data
        SESSION_TYPE='sqlalchemy',
        # User Configuration
        USER_APP_NAME="Mobilize CRM",
        USER_ENABLE_EMAIL=True,
        USER_ENABLE_USERNAME=False,
        # OAuth Configuration
        BASE_URL=os.environ.get('BASE_URL', 'http://localhost:5000'),
        GOOGLE_CLIENT_ID=secrets.get('GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID')),
        GOOGLE_CLIENT_SECRET=secrets.get('GOOGLE_CLIENT_SECRET', os.environ.get('GOOGLE_CLIENT_SECRET')),
        # Email Configuration
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True') == 'True',
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@mobilize-crm.org'),
        # Rate Limiting Configuration
        RATELIMIT_STRATEGY='fixed-window',
        RATELIMIT_DEFAULT='200 per hour',
        # Debugging options
        DEBUG_OAUTH=os.environ.get('DEBUG_OAUTH', 'False').lower() == 'true'
    )
    
    # Enable CORS for the application
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Log the database connection string (with sensitive parts masked)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url:
        # Mask the password in the connection string for logging
        masked_url = db_url
        if '@' in db_url and ':' in db_url.split('@')[0]:
            prefix = db_url.split('@')[0]
            user_part = prefix.split(':')[0]
            masked_url = f"{user_part}:******@{db_url.split('@')[1]}"
        app.logger.info(f"Database URL (masked): {masked_url}")
    
    try:
        # Initialize Flask extensions
        db.init_app(app)
        migrate.init_app(app, db)
        cors.init_app(app)
        csrf.init_app(app)
        limiter.init_app(app)
        login_manager.init_app(app)
        
        # Set login manager settings
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'info'
        
        # Check if database tables should be created
        skip_db_init = os.environ.get('SKIP_DB_INIT', 'True').lower() == 'true'
        app.logger.info(f"SKIP_DB_INIT is set to: {skip_db_init}")
        
        # Create all database tables (if they don't exist)
        if not skip_db_init:
            app.logger.info("Creating database tables...")
            with app.app_context():
                try:
                    db.create_all()
                    app.logger.info("Database tables created successfully")
                except Exception as e:
                    app.logger.error(f"Error creating database tables: {str(e)}")
        else:
            app.logger.info("Skipping database initialization...")
        
        # Configure URL handling
        app.url_map.strict_slashes = False
        
        # Initialize cache - based on config settings
        configure_cache(app)
        
        # Ensure Firebase configuration is properly set before initializing
        firebase_config = {
            'projectId': os.environ.get('FIREBASE_PROJECT_ID'),
            'apiKey': os.environ.get('FIREBASE_API_KEY'),
            'authDomain': os.environ.get('FIREBASE_AUTH_DOMAIN'),
            'storageBucket': os.environ.get('FIREBASE_STORAGE_BUCKET')
        }
        app.config['FIREBASE_CONFIG'] = firebase_config
        app.logger.info(f"Setting up Firebase with project ID: {firebase_config['projectId']}")
    
    except Exception as e:
        app.logger.error(f"Error during application initialization: {str(e)}")
        # Continue even if there are errors, so at least the health endpoints work
    
    try:
        # Register blueprints
        # ... existing code ...
        
        # Configure URL handling
        app.url_map.strict_slashes = False
        
        # Initialize cache - based on config settings
        configure_cache(app)
        
        # Configure secure headers with Talisman
        csp = {
            'default-src': [
                "'self'",
                'https://cdn.jsdelivr.net',
                'https://fonts.googleapis.com',
                'https://fonts.gstatic.com',
            ],
            'script-src': [
                "'self'",
                "'unsafe-inline'",
                'https://cdn.jsdelivr.net',
                'https://www.google-analytics.com',
            ],
            'style-src': [
                "'self'",
                "'unsafe-inline'",
                'https://cdn.jsdelivr.net',
                'https://fonts.googleapis.com',
            ],
            'img-src': [
                "'self'",
                'data:',
                'https://www.google-analytics.com',
            ],
            'font-src': [
                "'self'",
                'data:',
                'https://cdn.jsdelivr.net',
                'https://fonts.gstatic.com',
            ]
        }
        
        # Only enable Talisman in production
        if app.config.get('ENV') == 'production':
            talisman.init_app(
                app,
                force_https=True,
                content_security_policy=csp,
                content_security_policy_nonce_in=['script-src'],
                feature_policy={
                    'geolocation': "'none'",
                    'microphone': "'none'",
                    'camera': "'none'"
                },
                session_cookie_secure=True,
                session_cookie_http_only=True
            )
        else:
            # In development, still use Talisman but with less strict settings
            talisman.init_app(
                app,
                force_https=False,  # No HTTPS in dev
                content_security_policy=None,  # Disable CSP in dev for easier debugging
                feature_policy=None,
                session_cookie_secure=False
            )
        
        # Import models to ensure they are registered with SQLAlchemy
        from app.models import (
            User, Contact, Person, Church, Office,
            Task, Communication, EmailSignature, GoogleToken
        )
        
        # Setup model relationships
        with app.app_context():
            setup_relationships()
            if not skip_db_init:
                app.logger.info("Creating database tables again (within app context)...")
                db.create_all()
            else:
                app.logger.info("Skipping database initialization within app context...")
        
        # Setup login manager
        login_manager.session_protection = 'strong'
        
        @login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # Initialize JWT
        jwt.init_app(app)
        
        # Initialize Firebase
        init_firebase(app)
        
        # Initialize scheduler
        init_scheduler(app)
        
        # Register API blueprints
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        
        # Register API routes - Use the API blueprint directly to avoid double registration
        from app.routes.api.v1 import api_bp
        app.register_blueprint(api_bp, url_prefix='/api/v1')
        
        # Register route blueprints with their prefixes
        url_prefixes = {
            'dashboard': '/',  # Root URL for dashboard
            'admin': '/admin',
            'people': '/people',
            'churches': '/churches',
            'communications': '/communications',
            'tasks': '/tasks',
            'google_sync': '/google_sync',
            'settings': '/settings',
            'pipeline': '/pipeline',
            'reports': '/reports',
            'emails': '/emails',
            'onboarding': '/onboarding',
        }
        
        # Register all blueprints from routes/__init__.py
        for bp in blueprints:
            prefix = url_prefixes.get(bp.name, '/' + bp.name)
            app.register_blueprint(bp, url_prefix=prefix)
        
        # Register template filters and functions
        register_filters(app)
        register_template_functions(app)
        
        # Context processors
        @app.context_processor
        def inject_now():
            return {'now': datetime.datetime.now()}
        
        # Add the csrf_token to the template context
        @app.context_processor
        def inject_csrf_token():
            return dict(csrf_token=generate_csrf())
        
        # Determine if we're in production
        is_production = app.config.get('ENV') == 'production'

        # Configure session for better cross-domain compatibility
        # Use a longer session lifetime
        app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
        
        # Configure session cookie settings
        # Set SameSite to None to allow cross-domain cookies, but only in production
        if is_production:
            app.config['SESSION_COOKIE_SAMESITE'] = 'None'
            # Session cookies must be secure when SameSite is None
            app.config['SESSION_COOKIE_SECURE'] = True
        else:
            # For development
            app.config['SESSION_COOKIE_SECURE'] = False
            app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
        
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        
        # Handle request before processing to make session permanent
        @app.before_request
        def make_session_permanent():
            session.permanent = True
        
        # Error handlers
        @app.errorhandler(404)
        def not_found_error(error):
            return jsonify({'error': 'Not found'}), 404

        @app.errorhandler(500)
        def internal_error(error):
            db.session.rollback()
            return jsonify({'error': 'Internal server error'}), 500

        @app.errorhandler(401)
        def unauthorized_error(error):
            return jsonify({'error': 'Unauthorized'}), 401

        @app.errorhandler(400)
        def bad_request_error(error):
            return jsonify({'error': 'Bad request'}), 400

        # Setup Firebase (if configured)
        firebase_setup(app)
        
        # Setup the main pipelines on startup and migrate contacts
        with app.app_context():
            try:
                db.create_all()  # Create tables if they don't exist
                setup_main_pipelines()
                
                # Only migrate contacts to main pipelines if not in development
                if not app.debug:
                    from sqlalchemy import inspect
                    inspector = inspect(db.engine)
                    if 'pipelines' in inspector.get_table_names() and 'pipeline_stages' in inspector.get_table_names():
                        migrate_contacts_to_main_pipeline()
                    else:
                        app.logger.warning("Skipping contact migration - required tables don't exist yet")
                
                # Ensure all churches are in the church pipeline
                init_church_pipeline(app)
                
                app.logger.info("Pipeline initialization complete")
            except Exception as e:
                app.logger.error(f"Error initializing pipelines: {str(e)}")

        # Register template utilities
        register_template_utilities(app)
        
        # Register CLI commands
        register_commands(app)

        # Add stats to global context for sidebar badges
        @app.before_request
        def before_request():
            """Add stats to global context for sidebar badges."""
            if current_user.is_authenticated:
                try:
                    from app.routes.dashboard import get_dashboard_stats
                    g.stats = get_dashboard_stats()
                except Exception as e:
                    app.logger.error(f"Error getting dashboard stats: {str(e)}")
                    g.stats = {
                        'people_count': 0,
                        'church_count': 0,
                        'pending_tasks': 0,
                        'overdue_tasks': 0,
                        'recent_communications': 0
                    }
            else:
                g.stats = None

        return app 
    except Exception as e:
        app.logger.error(f"Error during application initialization: {str(e)}")
        # Continue even if there are errors, so at least the health endpoints work
        return app 