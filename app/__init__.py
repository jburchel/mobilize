import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.config import config, setup_logging
from app.services.firebase import init_firebase
from app.extensions import db, migrate, cors
from app.auth.routes import auth_bp
from app.routes import test_bp, admin_bp, dashboard_bp
from app.models.relationships import setup_relationships
from app.models.user import User

login_manager = LoginManager()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize Firebase
    init_firebase(app)
    
    # Setup logging
    setup_logging(app)
    
    # Set up model relationships
    with app.app_context():
        setup_relationships()
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(test_bp, url_prefix='/test')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    return app 