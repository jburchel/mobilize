import os
from pathlib import Path
from flask import current_app
from app.extensions import db

# Get the application root directory
ROOT_DIR = Path(__file__).parent.parent.parent

def init_db(app):
    """Initialize database configuration."""
    if app.config['ENV'] == 'production':
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_CONNECTION_STRING')
    else:
        # Use SQLite for development
        sqlite_path = os.path.join(app.instance_path, 'mobilize_crm.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_path}'
        # Ensure the instance folder exists
        os.makedirs(app.instance_path, exist_ok=True)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the SQLAlchemy app
    db.init_app(app)

def get_db():
    """Get the database instance."""
    if 'db' not in current_app.extensions:
        raise RuntimeError('Database not initialized. Call init_db() first.')
    return current_app.extensions['db'].db

def close_db(e=None):
    """Close the database connection."""
    db = current_app.extensions.get('db')
    if db is not None:
        db.session.remove()

# Database configurations
class DatabaseConfig:
    # Default to SQLite for development
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{ROOT_DIR}/instance/mobilize_crm.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('FLASK_ENV') == 'development' 