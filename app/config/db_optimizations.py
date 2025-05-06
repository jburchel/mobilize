"""Database connection optimizations for production environments."""

from flask import current_app
from sqlalchemy import event
from sqlalchemy.pool import QueuePool

def optimize_db_connections(app):
    """Configure optimized database connection settings for production.
    
    This function sets up connection pooling and other optimizations
    to improve database performance in production environments.
    """
    # Only apply optimizations in production
    # Check environment in a way compatible with newer Flask versions
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        current_app.logger.info("Database optimizations not applied in non-production environment")
        return
    
    current_app.logger.info("Applying database connection optimizations for production")
    
    # Configure SQLAlchemy connection pooling
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        # Set a reasonable pool size
        'pool_size': 10,  # Default number of connections to maintain
        'max_overflow': 20,  # Allow up to this many extra connections when needed
        'pool_timeout': 30,  # Seconds to wait before giving up on getting a connection
        'pool_recycle': 1800,  # Recycle connections after 30 minutes to prevent stale connections
        'pool_pre_ping': True,  # Check connection validity before using from pool
        'poolclass': QueuePool,  # Use QueuePool for connection pooling
    }
    
    current_app.logger.info(f"Database connection pool configured with size={app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size']}, "
                           f"max_overflow={app.config['SQLALCHEMY_ENGINE_OPTIONS']['max_overflow']}")

def setup_db_event_listeners(engine):
    """Set up event listeners for database connection management."""
    @event.listens_for(engine, 'connect')
    def optimize_postgres_connection(dbapi_connection, connection_record):
        """Optimize PostgreSQL connection parameters."""
        # Disable synchronous commits for better performance
        # This is safe for read-heavy applications but may risk some data loss
        # in case of server crash for recent writes
        cursor = dbapi_connection.cursor()
        cursor.execute("SET synchronous_commit TO OFF")
        cursor.close()

def register_db_optimizations(app, db):
    """Register all database optimizations.
    
    Call this function after db.init_app(app) in your application factory.
    """
    optimize_db_connections(app)
    
    # Set up event listeners after engine is created
    with app.app_context():
        setup_db_event_listeners(db.engine)
        current_app.logger.info("Database event listeners configured for performance optimization")
