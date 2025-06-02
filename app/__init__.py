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
from werkzeug.middleware.proxy_fix import ProxyFix # Add ProxyFix import
# Configuration imports
from app.config.config import Config, TestingConfig, ProductionConfig, DevelopmentConfig  # noqa: F401
from app.config.logging_config import setup_logging  # noqa: F401
from app.extensions import db, migrate, cors, login_manager, jwt, csrf, limiter, talisman, configure_cache, scheduler
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
from app.utils.db_transaction_fix import init_app as init_db_transaction_fix

# Import performance optimizations
from app.config.performance_optimizations import optimize_flask_app
from app.config.static_optimizations import optimize_static_files
from app.config.database_optimizations import optimize_database_queries
from app.config.connection_pool import optimize_connection_pool

# Load environment variables based on the current environment
env = os.environ.get('FLASK_ENV', 'development')
if env == 'production':
    load_dotenv(find_dotenv(".env.production"), override=True)
    logging.info("Loaded production environment variables from .env.production")
else:
    load_dotenv(find_dotenv(".env.development"), override=True)
    logging.info("Loaded development environment variables from .env.development")

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
    # Apply ProxyFix to handle X-Forwarded-Proto and X-Forwarded-Host headers
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Load configuration (Keep logic from development)
    env = os.getenv('FLASK_ENV', 'development')
    app.logger.info(f"[ENV_DEBUG] FLASK_ENV is '{env}'. Entered '{env}' configuration block.")
    secrets = access_secrets()
    
    # Debug: List all environment variables to help troubleshoot
    app.logger.info("[ENV_DEBUG] Listing all environment variable names:")
    env_var_names = list(os.environ.keys())
    for name in env_var_names:
        if 'client' in name.lower() or 'google' in name.lower() or 'secret' in name.lower():
            # Only log names that might be related to our issue, for security
            app.logger.info(f"[ENV_DEBUG] Found environment variable: {name}")
    
    # Check if we're running in Cloud Run
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    # Log database connection information for debugging
    if is_cloud_run:
        app.logger.info("Running in Cloud Run environment")
        if os.environ.get('DATABASE_URL'):
            # Mask password for logging
            db_url = os.environ.get('DATABASE_URL', '')
            masked_url = db_url.replace('://', '://****:****@') if '://' in db_url else db_url
            app.logger.info(f"DATABASE_URL is set to: {masked_url}")
        else:
            app.logger.warning("DATABASE_URL is not set in Cloud Run environment")

    if test_config:
        if isinstance(test_config, dict):
            app.config.from_object(TestingConfig)
            app.config.update(test_config)
        else:
            app.config.from_object(test_config)
    elif env == 'production':
        app.logger.info(f"[ENV_DEBUG] FLASK_ENV is '{env}'. Entered 'production' configuration block.")
        app.config.from_object(ProductionConfig)
        # Always use DATABASE_URL directly from environment variables for production
        db_uri = os.environ.get('DATABASE_URL')
        if not db_uri:
            app.logger.error("CRITICAL: DATABASE_URL is not set for production environment!")
        
        # Add OAuth credentials to app config - try multiple environment variable name formats
        # The issue might be that environment variables with hyphens don't work as expected
        possible_client_id_names = [
            'mobilize-google-client-id',  # Original name with hyphens
            'MOBILIZE_GOOGLE_CLIENT_ID',  # Uppercase with underscores (common env var format)
            'mobilize_google_client_id',  # Lowercase with underscores
            'GOOGLE_CLIENT_ID',          # Direct name without prefix
            'google-client-id'           # Lowercase with hyphens, no prefix
        ]
        
        possible_client_secret_names = [
            'mobilize-google-client-secret',  # Original name with hyphens
            'MOBILIZE_GOOGLE_CLIENT_SECRET',  # Uppercase with underscores
            'mobilize_google_client_secret',  # Lowercase with underscores
            'GOOGLE_CLIENT_SECRET',          # Direct name without prefix
            'google-client-secret'           # Lowercase with hyphens, no prefix
        ]
        
        # Try each possible name for client ID
        raw_env_client_id = None
        for var_name in possible_client_id_names:
            value = os.environ.get(var_name)
            if value:
                raw_env_client_id = value
                app.logger.info(f"[AUTH_DEBUG_ENV] Found Google Client ID in environment variable: {var_name}")
                break
        
        # Try each possible name for client secret
        raw_env_client_secret_val = None
        for var_name in possible_client_secret_names:
            value = os.environ.get(var_name)
            if value:
                raw_env_client_secret_val = value
                app.logger.info(f"[AUTH_DEBUG_ENV] Found Google Client Secret in environment variable: {var_name}")
                break
                
        app.logger.info(f"[AUTH_DEBUG_ENV] Google Client ID found: {bool(raw_env_client_id)}")
        app.logger.info(f"[AUTH_DEBUG_ENV] Raw os.environ.get('mobilize-google-client-secret') exists: {bool(raw_env_client_secret_val)}")
        if not raw_env_client_id:
            app.logger.error("[AUTH_DEBUG_ENV] CRITICAL: 'mobilize-google-client-id' NOT FOUND in os.environ!")
        
        app.config.update(
            SECRET_KEY=secrets.get('SECRET_KEY', app.config.get('SECRET_KEY')),
            SQLALCHEMY_DATABASE_URI=db_uri,
            GOOGLE_CLIENT_ID=raw_env_client_id, # Use the already fetched value
            GOOGLE_CLIENT_SECRET=raw_env_client_secret_val, # Use the already fetched value
        )
        app.logger.info(f'Database URI set to: {db_uri and db_uri[:10]}...') # This log was seen

        # ---- START DETAILED AUTH LOGGING (POST-CONFIG) ----
        loaded_config_client_id = app.config.get('GOOGLE_CLIENT_ID')
        config_client_secret_is_set = bool(app.config.get('GOOGLE_CLIENT_SECRET')) # Check if it's set in config
        app.logger.info(f"[AUTH_DEBUG_CONFIG] app.config.get('GOOGLE_CLIENT_ID'): '{loaded_config_client_id}'")
        app.logger.info(f"[AUTH_DEBUG_CONFIG] app.config.get('GOOGLE_CLIENT_SECRET') is set in app.config: {config_client_secret_is_set}")

        if not loaded_config_client_id: # Check after trying to load into app.config
            app.logger.error("[AUTH_DEBUG_CONFIG] CRITICAL: GOOGLE_CLIENT_ID is NOT SET in app.config (after attempting to set from env)!")
        # ---- END DETAILED AUTH LOGGING (POST-CONFIG) ----
    elif env == 'testing':
        app.config.from_object(TestingConfig)
    else: # Development or default
        app.config.from_object(DevelopmentConfig)
        # Ensure loaded .env.development values override DevelopmentConfig defaults
        app.config.update({k: v for k, v in os.environ.items() if k in app.config})

    # Ensure required environment variables are present, falling back to config if necessary
    # Example: Database URI
    # Always use DATABASE_URL directly from environment variables for production
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        app.logger.error("CRITICAL: DATABASE_URL is not set!")
    
    # Print database connection info for debugging
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')
    masked_uri = db_uri.replace("://", "://***:***@") if "://" in db_uri else db_uri
    app.logger.info(f"[DATABASE CONNECTION] Using database: {masked_uri}")

    # Ensure SQLALCHEMY_TRACK_MODIFICATIONS is disabled
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    # Initialize Flask extensions - only if they haven't been initialized yet
    # Check if db is already initialized with this app
    if not hasattr(app, '_got_first_request'):
        # Flask-SQLAlchemy
        try:
            db.init_app(app)
            app.logger.info("Initialized Flask-SQLAlchemy extension.")
        except RuntimeError as e:
            app.logger.info(f"Flask-SQLAlchemy already initialized: {str(e)}")
        
        # Flask-Migrate
        migrate.init_app(app, db)  # Flask-Migrate needs both app and db
        
        # Flask-CORS
        # Adjust CORS origins as needed for production
        cors.init_app(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})
        
        # Flask-Login
        login_manager.init_app(app)
        
        # Flask-JWT-Extended
        jwt.init_app(app)
        
        # Flask-WTF CSRF Protection
        csrf.init_app(app)
        
        # APScheduler
        if not app.config.get('TESTING', False): # APScheduler can cause issues in tests if not handled
            scheduler.init_app(app)
            scheduler.start()
        
        # Flask-Limiter
        limiter.init_app(app)
        
        # Flask-Talisman (HTTPS/security headers)
        # Basic Talisman setup. Review and strengthen CSP for production.
        talisman.init_app(app, content_security_policy=app.config.get('TALISMAN_CSP', None))
        
        app.logger.info("All Flask extensions initialized successfully.")

    # Initialize mail: Use MailStub for dev/test, real Mail for prod
    if app.config.get('ENV') in ['development', 'testing'] or not app.config.get('MAIL_SERVER') or app.config.get('TESTING'):
        from app.extensions import MailStub
        app.mail = MailStub() # Assign to app.mail directly for consistency
        app.logger.info("Using MailStub for email.")
    else:
        from app.extensions import mail # import mail instance
        mail.init_app(app)
        app.mail = mail # Assign to app.mail
        app.logger.info("Flask-Mail initialized for sending emails.")
    
    configure_cache(app) # This initializes cache.init_app(app) internally

    # Initialize our custom database transaction fix *after* db is initialized
    # This fixes the 'Textual SQL expression' error with SELECT 1
    init_db_transaction_fix(app)
    app.logger.info("Initialized Flask extensions and DB transaction fix.")

    # Celery Configuration
    # Import celery instance from app.extensions
    from app.extensions import celery as celery_app_instance # Use an alias

    # Define a context-aware task base class
    class ContextTask(celery_app_instance.Task):
        abstract = True # Ensure this is an abstract class
        def __call__(self, *args, **kwargs):
            with app.app_context(): # Ensures task runs within Flask app context
                return self.run(*args, **kwargs)

    # Get Celery broker URL from environment variables
    celery_broker_url = os.environ.get('CELERY_BROKER_URL')

    if not celery_broker_url:
        # Log a warning if no broker URL is set and configure for eager execution
        logging.warning(
            "CELERY_BROKER_URL not set or empty. "
            "Celery will run tasks eagerly (synchronously) in the current process. "
            "This is suitable for development or environments without a message broker."
        )
        celery_app_instance.conf.update(
            task_always_eager=True,
            task_eager_propagates=True  # If True, exceptions in eager tasks will propagate
        )
    else:
        # Log that Celery is configured with a broker
        logging.info(f"Celery configured with broker URL: {celery_broker_url}")
        celery_app_instance.conf.update(
            broker_url=celery_broker_url,
            # Use broker_url as default for result_backend if CELERY_RESULT_BACKEND is not set
            result_backend=os.environ.get('CELERY_RESULT_BACKEND', celery_broker_url)
        )
    
    # Set the custom context-aware task as the default base class for all tasks
    celery_app_instance.Task = ContextTask

    # Initialize Flask extensions
    db.init_app(app)
    migrate.init_app(app, db) # Flask-Migrate needs both app and db
    # Adjust CORS origins as per your actual requirements for production
    cors.init_app(app, resources={r"/*": {"origins": "*"}}) # Example: Allow all for now, refine later
    login_manager.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app) # Crucial for csrf_token() in templates
    limiter.init_app(app)
    # Basic Talisman setup, review and strengthen CSP for production
    talisman.init_app(app, content_security_policy=None, force_https=os.environ.get('FLASK_ENV') == 'production') 
    configure_cache(app) # This function from extensions.py calls cache.init_app(app)
    # mail.init_app(app) # Uncomment and configure if direct mail sending is needed here
    # scheduler.init_app(app) # Uncomment if APScheduler is used and needs init here
    # if os.environ.get('FLASK_ENV') != 'testing' and not (scheduler.running and scheduler.app):
    #    if not scheduler.running:
    #        scheduler.start()
    #    elif scheduler.app != app:
    #        scheduler.shutdown(wait=False)
    #        scheduler.init_app(app)
    #        scheduler.start()

    # --- Keep Health Check and Debug Endpoints from main ---
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'time': datetime.datetime.now().isoformat(),
            'message': 'Basic health check passed'
        }), 200

    @app.route('/api/db-test', methods=['GET'])
    def db_test():
        try:
            from sqlalchemy import text
            result = db.session.execute(text('SELECT 1')).fetchone()
            return jsonify({
                'status': 'success',
                'message': 'Database connection successful',
                'result': result[0] if result else None,
                'database_url': app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set').split('@')[1] if '@' in app.config.get('SQLALCHEMY_DATABASE_URI', '') else 'Masked'
            })
        except Exception as e:
            app.logger.error(f"Database connection test failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection failed',
                'error': str(e)
            }), 500

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
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://cdn.jsdelivr.net', 'https://www.google-analytics.com'],
            'style-src': ["'self'", "'unsafe-inline'", 'https://cdn.jsdelivr.net', 'https://fonts.googleapis.com'],
            'img-src': ["'self'", 'data:', 'https://www.google-analytics.com'],
            'font-src': ["'self'", 'data:', 'https://cdn.jsdelivr.net', 'https://fonts.gstatic.com'],
            # Add these new directives to allow drag and drop functionality
            'connect-src': ["'self'"],
            'worker-src': ["'self'"],
            'frame-src': ["'self'"],
            # Use a more permissive child-src policy as a fallback for older browsers
            'child-src': ["'self'"]
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
    # Register our simplified communications blueprint
    from app.routes.communications_simple import communications_simple_bp
    app.register_blueprint(communications_simple_bp, url_prefix='/communications_simple')
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
    optimize_connection_pool(app, db)
    
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
        
        # Initialize cached_stats if not exists
        if not hasattr(g, 'cached_stats'):
            g.cached_stats = {}
            
        if current_user.is_authenticated:
            # Check if user needs profile image update from Google
            try:
                if not current_user.profile_image and hasattr(current_user, 'email'):
                    # Check if user has Google token
                    from app.models.google_token import GoogleToken
                    token = GoogleToken.query.filter_by(user_id=current_user.id).first()
                    
                    if token:
                        # Try to get profile image from Google
                        try:
                            from app.auth.google_oauth import get_google_credentials
                            credentials = get_google_credentials(current_user.id)
                            
                            if credentials:
                                from googleapiclient.discovery import build
                                service = build('oauth2', 'v2', credentials=credentials)
                                user_info = service.userinfo().get().execute()
                                
                                if user_info and 'picture' in user_info and user_info['picture']:
                                    app.logger.info(f"Auto-updating profile image for user {current_user.id} from Google")
                                    
                                    # Download and store the image locally instead of just storing the URL
                                    try:
                                        import requests
                                        import os
                                        from werkzeug.utils import secure_filename
                                        from flask import url_for
                                        
                                        # Create profile images directory if it doesn't exist
                                        profile_images_dir = os.path.join(app.static_folder, 'profile_images')
                                        os.makedirs(profile_images_dir, exist_ok=True)
                                        
                                        # Download the image
                                        response = requests.get(user_info['picture'])
                                        if response.status_code == 200:
                                            # Generate a unique filename
                                            filename = f"user_{current_user.id}_profile.jpg"
                                            secure_name = secure_filename(filename)
                                            file_path = os.path.join(profile_images_dir, secure_name)
                                            
                                            # Save the image
                                            with open(file_path, 'wb') as f:
                                                f.write(response.content)
                                            
                                            # Update the user's profile image with the local path
                                            current_user.profile_image = url_for('static', filename=f'profile_images/{secure_name}', _external=True)
                                            db.session.commit()
                                            app.logger.info(f"Successfully downloaded and stored Google profile image for user {current_user.id}")
                                    except Exception as e:
                                        app.logger.warning(f"Error downloading Google profile image: {str(e)}")
                                        # Fallback to just storing the URL if download fails
                                        current_user.profile_image = user_info['picture']
                                        db.session.commit()
                        except Exception as e:
                            app.logger.warning(f"Could not fetch Google profile image: {str(e)}")
            except Exception as e:
                app.logger.error(f"Error in profile image check: {str(e)}")
            
            # Only calculate stats if they haven't been calculated yet
            if not hasattr(g, 'stats') or g.stats is None:
                g.stats = {
                    'tasks_count': current_user.count_owned_records('tasks'),
                    'churches_count': current_user.count_owned_records('churches'),
                    'people_count': current_user.count_owned_records('people')
                }
        else:
            g.stats = None

    return app