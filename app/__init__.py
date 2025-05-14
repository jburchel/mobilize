import os
import logging
import datetime
import sys  # noqa: F401
import time  # noqa: F401
# Flask imports - these are used throughout the application
from flask import Flask, Blueprint, g, jsonify, request, current_app, render_template, session  # noqa: F401
from flask_cors import CORS
from flask_migrate import Migrate  # noqa: F401
from flask_login import LoginManager, current_user  # noqa: F401
from flask_jwt_extended import JWTManager  # noqa: F401
from flask_wtf.csrf import CSRFProtect, generate_csrf  # noqa: F401
from flask_limiter import Limiter  # noqa: F401
from flask_limiter.util import get_remote_address  # noqa: F401
from flask_talisman import Talisman  # noqa: F401
from dotenv import load_dotenv, find_dotenv
# Configuration imports
from app.config.config import Config, TestingConfig, ProductionConfig, DevelopmentConfig  # noqa: F401
from app.config.logging_config import setup_logging  # noqa: F401
from app.extensions import db, migrate, cors, login_manager, jwt, csrf, limiter, talisman, configure_cache
from app.auth.firebase import init_firebase
from app.auth.routes import auth_bp
from app.routes import blueprints
from app.models.relationships import setup_relationships
from app.tasks.scheduler import init_scheduler
from app.utils.filters import register_filters, register_template_functions
from app.utils.firebase import firebase_setup
from app.utils.context_processors import register_template_utilities
from app.utils.setup_main_pipelines import setup_main_pipelines
from app.utils.migrate_contacts_to_main_pipeline import migrate_contacts_to_main_pipeline
from app.utils.ensure_church_pipeline import init_app as init_church_pipeline
from app.cli import register_commands

# Import performance optimizations
from app.config.performance_optimizations import optimize_flask_app
from app.config.static_optimizations import optimize_static_files
from app.config.database_optimizations import optimize_database_queries

# Load environment variables from .env.development first
load_dotenv(find_dotenv(".env.development"), override=True) # Keep from main, ensure override=True

# Function to access secrets (kept from development branch logic)
def access_secrets():
    secrets = {}
    try:
        if os.environ.get('FLASK_ENV') == 'production':
            from google.cloud import secretmanager
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'mobilize-crm')
            client = secretmanager.SecretManagerServiceClient()
            
            secret_names = ['SECRET_KEY', 'DATABASE_URL', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
            for name in secret_names:
                secret_path = f"projects/{project_id}/secrets/{name}/versions/latest"
                try:
                    response = client.access_secret_version(request={"name": secret_path})
                    secrets[name] = response.payload.data.decode('UTF-8')
                except Exception as e:
                    logging.warning(f"Could not access secret: {name}, error: {str(e)}")
    except Exception as e:
        logging.error(f"Error initializing secret manager: {str(e)}")
    return secrets

# Initialize extensions that aren't in extensions.py
# (Remove this as we're using the ones from extensions.py)

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)

    # Load configuration (Keep logic from development)
    env = os.getenv('FLASK_ENV', 'development')
    secrets = access_secrets()
    
    # Check if we're running in Cloud Run
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    # Ensure DB_CONNECTION_STRING is properly set in environment variables
    if is_cloud_run and os.environ.get('DB_CONNECTION_STRING'):
        # Make sure DATABASE_URL is set for SQLAlchemy
        if not os.environ.get('DATABASE_URL'):
            os.environ['DATABASE_URL'] = os.environ.get('DB_CONNECTION_STRING')
            app.logger.info('Set DATABASE_URL from DB_CONNECTION_STRING for Cloud Run')

    if test_config:
        if isinstance(test_config, dict):
            app.config.from_object(TestingConfig)
            app.config.update(test_config)
        else:
            app.config.from_object(test_config)
    elif env == 'production':
        app.config.from_object(ProductionConfig)
        # Prioritize DB_CONNECTION_STRING for Cloud Run
        db_uri = os.environ.get('DB_CONNECTION_STRING')
        if not db_uri:
            db_uri = secrets.get('DATABASE_URL', os.environ.get('DATABASE_URL'))
        
        app.config.update(
            SECRET_KEY=secrets.get('SECRET_KEY', app.config.get('SECRET_KEY')),
            SQLALCHEMY_DATABASE_URI=db_uri,
            GOOGLE_CLIENT_ID=secrets.get('GOOGLE_CLIENT_ID', os.environ.get('GOOGLE_CLIENT_ID')),
            GOOGLE_CLIENT_SECRET=secrets.get('GOOGLE_CLIENT_SECRET', os.environ.get('GOOGLE_CLIENT_SECRET')),
        )
        app.logger.info(f'Database URI set to: {db_uri and db_uri[:10]}...')
    elif env == 'testing':
        app.config.from_object(TestingConfig)
    else: # Development or default
        app.config.from_object(DevelopmentConfig)
        # Ensure loaded .env.development values override DevelopmentConfig defaults
        app.config.update({k: v for k, v in os.environ.items() if k in app.config})

    # Ensure required environment variables are present, falling back to config if necessary
    # Example: Database URI
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
         app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', os.environ.get('DB_CONNECTION_STRING'))
         if not app.config['SQLALCHEMY_DATABASE_URI']:
             app.logger.error("CRITICAL: SQLALCHEMY_DATABASE_URI is not set!")
    
    # Print database connection info for debugging
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
    masked_uri = db_uri.replace("://", "://***:***@") if "://" in db_uri else db_uri
    app.logger.info(f"[DATABASE CONNECTION] Using database: {masked_uri}")

    # Ensure SQLALCHEMY_TRACK_MODIFICATIONS is disabled
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    # --- Keep Health Check and Debug Endpoints from main ---
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'message': 'Basic health check passed'
        }), 200

    @app.route('/api/direct-db-test', methods=['GET'])
    def direct_db_test():
        from sqlalchemy import create_engine, text
        import urllib.parse
        results = []
        # Method 1: Standard pooler with postgres.reference username
        try:
            username1 = "postgres.fwnitauuyzxnsvgsbrzr"
            password1 = "Fruitin2025" # Consider putting this in secrets/env
            host1 = "aws-0-us-east-1.pooler.supabase.com"
            url1 = f"postgresql://{username1}:{urllib.parse.quote_plus(password1)}@{host1}:5432/postgres?sslmode=require"
            engine1 = create_engine(url1)
            with engine1.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                results.append({"method": "standard_pooler", "status": "success", "username": username1})
        except Exception as e:
            results.append({"method": "standard_pooler", "status": "error", "username": username1, "error": str(e)})
        # Method 2: Try with just 'postgres' username
        try:
            username2 = "postgres"
            password2 = "Fruitin2025" # Consider putting this in secrets/env
            host2 = "aws-0-us-east-1.pooler.supabase.com"
            url2 = f"postgresql://{username2}:{urllib.parse.quote_plus(password2)}@{host2}:5432/postgres?sslmode=require"
            engine2 = create_engine(url2)
            with engine2.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                # Fetch result to confirm connection works, but we don't need the value
                _ = result.fetchone()
                results.append({"method": "postgres_user", "status": "success", "username": username2})
        except Exception as e:
            results.append({"method": "postgres_user", "status": "error", "username": username2, "error": str(e)})
        # Method 3: Try direct connection format
        try:
            username3 = "postgres"
            password3 = "Fruitin2025" # Consider putting this in secrets/env
            host3 = "db.fwnitauuyzxnsvgsbrzr.supabase.co"
            url3 = f"postgresql://{username3}:{urllib.parse.quote_plus(password3)}@{host3}:5432/postgres?sslmode=require"
            engine3 = create_engine(url3)
            with engine3.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                row = result.fetchone()
                results.append({"method": "direct_connection", "status": "success", "username": username3})
        except Exception as e:
            results.append({"method": "direct_connection", "status": "error", "username": username3, "error": str(e)})
        return jsonify({
            "results": results,
            "message": "Tried multiple connection methods"
        })

    @app.route('/api/health-check', methods=['GET'])
    def api_health_check():
        status = {
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'database': 'unknown',
            'environment': os.environ.get('FLASK_ENV', 'unknown')
        }
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

    @app.route('/api/debug/db-config', methods=['GET'])
    def debug_db_config():
        db_url = os.environ.get('DATABASE_URL', 'not-set')
        db_conn = os.environ.get('DB_CONNECTION_STRING', 'not-set')
        def mask_password(url):
            if not url or url == 'not-set':
                return url
            if '@' in url and ':' in url.split('@')[0]:
                parts = url.split('@')
                user_parts = parts[0].split(':')
                return f"{user_parts[0]}:******@{parts[1]}"
            return url
        secret_db_url = 'not-loaded'
        try:
            if os.environ.get('FLASK_ENV') == 'production':
                 # (Secret manager logic kept from development - condensed for brevity)
                 secret_db_url = secrets.get('DATABASE_URL', 'Not found in secrets')
                 secret_db_url = mask_password(secret_db_url)
        except Exception as e:
            secret_db_url = f"Error: {str(e)}"
        config_db_url = mask_password(app.config.get('SQLALCHEMY_DATABASE_URI', 'not-set-in-config'))
        return jsonify({
            'env': os.environ.get('FLASK_ENV', 'unknown'),
            'database_url_masked': mask_password(db_url),
            'db_conn_string_masked': mask_password(db_conn),
            'secret_manager_url_masked': secret_db_url,
            'config_db_url_masked': config_db_url,
            'using_secret_manager': os.environ.get('FLASK_ENV') == 'production'
        })
    # --- End Health Check/Debug Endpoints ---

    # Enable CORS for the application
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/dashboard/*": {"origins": "*"}
    })

    # Log the database connection string (with sensitive parts masked)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url:
        masked_url = db_url
        if '@' in db_url and ':' in db_url.split('@')[0]:
            prefix = db_url.split('@')[0]
            user_part = prefix.split(':')[0]
            masked_url = f"{user_part}:******@{db_url.split('@')[1]}"
        app.logger.info(f"Database URL (masked): {masked_url}")
    else:
         app.logger.warning("SQLALCHEMY_DATABASE_URI not configured!")


    # Initialize Flask extensions (Combined section)
    try:
        # Initialize login_manager first, before any other extensions
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login_page'
        login_manager.login_message_category = 'info'
        
        @login_manager.user_loader
        def load_user(user_id):
            from app.models.user import User
            return User.query.get(int(user_id))

        # Then initialize other extensions
        db.init_app(app)
        migrate.init_app(app, db)
        cors.init_app(app)
        csrf.init_app(app)
        limiter.init_app(app)
        
        # Set up relationships before any database operations
        with app.app_context():
            setup_relationships()
            app.logger.info("Model relationships set up.")
        
        skip_db_init = os.environ.get('SKIP_DB_INIT', 'False').lower() == 'true' or app.config.get('TESTING')
        app.logger.info(f"SKIP_DB_INIT is set to: {skip_db_init}")

        if not skip_db_init:
            app.logger.info("Attempting to create database tables...")
            with app.app_context():
                try:
                    # Import all models needed for db.create_all() to work properly
                    # These imports are used by SQLAlchemy to discover models for table creation
                    from app.models import User, Contact, Person, Church, Office, Task, Communication, EmailSignature, GoogleToken, Role, Permission # noqa
                    db.create_all()
                    app.logger.info("Database tables checked/created successfully.")
                except Exception as e:
                    app.logger.error(f"Error during DB initialization: {str(e)}")
        else:
            app.logger.info("Skipping automatic database initialization.")

        app.url_map.strict_slashes = False
        configure_cache(app)

        # Configure Talisman (Keep logic from development)
        csp = {
            'default-src': ["'self'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com', 'https://fonts.gstatic.com'],
            'script-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://www.google-analytics.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
            'img-src': ["'self'", 'data:', 'https://www.google-analytics.com'],
            'font-src': ["'self'", 'data:', 'https://cdn.jsdelivr.net', 'https://fonts.gstatic.com']
        }
        if env == 'production':
            talisman.init_app(app, force_https=True, content_security_policy=csp,
                              content_security_policy_nonce_in=['script-src'],
                              feature_policy={'geolocation': "'none'", 'microphone': "'none'", 'camera': "'none'"},
                              session_cookie_secure=True, session_cookie_http_only=True)
        else:
            talisman.init_app(app, force_https=False, content_security_policy=None,
                              feature_policy=None, session_cookie_secure=False)

    except Exception as e:
        app.logger.error(f"Error during application extension initialization: {str(e)}")

    # --- MOVE ALL REGISTRATIONS BELOW THIS LINE ---

    jwt.init_app(app)
    init_firebase(app)
    init_scheduler(app)

    # Register all blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(auth_bp, url_prefix='/auth', name='auth_web')
    from app.routes.api.v1 import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    url_prefixes = { 'dashboard': '/', 'admin': '/admin', 'people': '/people', 'churches': '/churches',
                     'communications': '/communications', 'tasks': '/tasks', 'google_sync': '/google_sync',
                     'settings': '/settings', 'pipeline': '/pipeline', 'reports': '/reports',
                     'emails': '/emails', 'onboarding': '/onboarding', }
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
    @app.context_processor
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf())
    @app.context_processor
    def inject_pipeline_utilities():
        from app.extensions import db
        def get_pipeline_count(pipeline_id):
            from sqlalchemy import text
            result = db.session.execute(
                text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
                {"pipeline_id": pipeline_id}
            )
            return result.scalar() or 0
        return dict(get_pipeline_count=get_pipeline_count)

    # Session Configuration (Keep logic from development)
    is_production = app.config.get('ENV') == 'production'
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=1)
    if is_production:
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'
        app.config['SESSION_COOKIE_SECURE'] = True
    else:
        app.config['SESSION_COOKIE_SECURE'] = False
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Error handlers (Keep combined)
    @app.errorhandler(404)
    def not_found_error(error): return jsonify({'error': 'Not found'}), 404
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    @app.errorhandler(401)
    def unauthorized_error(error): return jsonify({'error': 'Unauthorized'}), 401
    @app.errorhandler(400)
    def bad_request_error(error): return jsonify({'error': 'Bad request'}), 400

    # Setup Firebase (if configured)
    firebase_setup(app)
    
    # Apply performance optimizations for production
    optimize_flask_app(app)
    optimize_static_files(app)
    optimize_database_queries(app)
    
    # Setup pipelines and migrate contacts (Keep logic from development)
    with app.app_context():
        try:
            # Ensure test users don't appear in production
            if app.config.get('FLASK_ENV') == 'production':
                app.config['DISABLE_TEST_USERS'] = True
                app.logger.info("Test users disabled in production environment")
                
            # Ensure tables exist before pipeline setup
            db.create_all()
            setup_main_pipelines()
            if not app.debug:
                from sqlalchemy import inspect
                inspector = inspect(db.engine)
                if 'pipelines' in inspector.get_table_names() and 'pipeline_stages' in inspector.get_table_names():
                    migrate_contacts_to_main_pipeline()
                else:
                    app.logger.warning("Skipping contact migration - required tables don't exist yet")
            init_church_pipeline(app)
            app.logger.info("Pipeline initialization complete")
        except Exception as e:
            app.logger.error(f"Error initializing pipelines: {str(e)}")

    # Register template utilities
    register_template_utilities(app)

    # Register CLI commands
    register_commands(app)
    
    # Initialize database query logging
    from app.utils.db_logger import init_app as init_db_logger
    init_db_logger(app)
    app.logger.info("Database query logging initialized")
    
    # Initialize activity logger middleware
    from app.middleware.activity_logger import ActivityLoggerMiddleware
    ActivityLoggerMiddleware(app)
    app.logger.info("Activity logger middleware initialized")

    # Add stats to global context for sidebar badges
    @app.before_request
    def before_request():
        if not hasattr(app, 'login_manager') or not app.login_manager:
            g.stats = None
            return
            
        if current_user.is_authenticated:
            g.stats = {
                'tasks_count': current_user.count_owned_records('tasks'),
                'churches_count': current_user.count_owned_records('churches'),
                'people_count': current_user.count_owned_records('people')
            }
        else:
            g.stats = None

    return app