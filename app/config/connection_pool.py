from sqlalchemy import event

def optimize_connection_pool(app, db):
    """
    Optimize database connection pool to prevent connection exhaustion.
    This is especially important for Supabase which has strict connection limits.
    """
    app.logger.info("Optimizing database connection pool")
    
    # Reduce the connection pool size to prevent exhaustion
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,  # Reduced from 10
        'max_overflow': 10,  # Reduced from 20
        'pool_timeout': 30,
        'pool_recycle': 600,  # Recycle connections after 10 minutes instead of 30
        'pool_pre_ping': True,  # Check connection validity before using it
    }
    
    # Set up event listeners to ensure connections are properly returned to the pool
    @event.listens_for(db.engine, 'checkout')
    def checkout(dbapi_connection, connection_record, connection_proxy):
        app.logger.debug("Connection checked out from pool")
    
    @event.listens_for(db.engine, 'checkin')
    def checkin(dbapi_connection, connection_record):
        app.logger.debug("Connection returned to pool")
    
    # Explicitly close connections at the end of requests
    @app.teardown_request
    def close_db_connection(exception=None):
        db.session.close()
        app.logger.debug("Database session closed at end of request")
    
    app.logger.info("Database connection pool optimization complete")
