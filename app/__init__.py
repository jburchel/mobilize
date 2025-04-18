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

# Initialize extensions that aren't in extensions.py
# (Remove this as we're using the ones from extensions.py)

def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DEBUG=os.environ.get('FLASK_DEBUG', 'False') == 'True',
        # Database Configuration
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI', 
                                              os.environ.get('DB_CONNECTION_STRING')),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Cache Configuration for session data
        SESSION_TYPE='sqlalchemy',
        # User Configuration
        USER_APP_NAME="Mobilize CRM",
        USER_ENABLE_EMAIL=True,
        USER_ENABLE_USERNAME=False,
        # OAuth Configuration
        BASE_URL=os.environ.get('BASE_URL', 'http://localhost:5000'),
        GOOGLE_CLIENT_ID=os.environ.get('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.environ.get('GOOGLE_CLIENT_SECRET'),
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
            db.create_all()
    else:
        app.logger.info("Skipping database initialization...")
    
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