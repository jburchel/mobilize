import os
import logging
import datetime
from flask import Flask, jsonify, render_template, request, g, current_app
from flask_migrate import Migrate
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import generate_csrf, CSRFProtect
from app.config.config import Config, TestingConfig, ProductionConfig
from app.config.logging_config import setup_logging
from app.auth.firebase import init_firebase
from app.extensions import db, migrate, cors, login_manager, jwt, csrf, Base
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
from app.cli import register_commands
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Apply configuration
    if isinstance(config_name, str):
        if config_name == 'development':
            app.config.from_object(Config)
        elif config_name == 'testing':
            app.config.from_object(TestingConfig)
        elif config_name == 'production':
            app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(config_name)
    
    # Configure URL handling
    app.url_map.strict_slashes = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    csrf.init_app(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models import (
        User, Contact, Person, Church, Office,
        Task, Communication, EmailSignature, GoogleToken
    )
    
    # Setup model relationships
    with app.app_context():
        setup_relationships()
        db.create_all()
    
    # Setup login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
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
                
        except Exception as e:
            app.logger.error(f"Error during startup database setup: {str(e)}")

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