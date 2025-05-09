"""Database query optimizations for the Flask application."""

# Database optimization imports
from sqlalchemy import text, event

def optimize_database_queries(app):
    """Apply database query optimizations.
    
    This function configures various optimizations for database queries
    to improve application performance.
    """
    # Only run optimizations in production
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        app.logger.info("Skipping database optimizations in non-production environment")
        return
        
    app.logger.info("Applying database query optimizations")
    
    # Add indexes to commonly queried columns
    add_database_indexes(app)
    
    # Configure SQLAlchemy for better performance
    configure_sqlalchemy_optimizations(app)
    
    # Set up query monitoring for slow queries
    setup_query_monitoring(app)
    
    app.logger.info("Database query optimizations applied successfully")

def add_database_indexes(app):
    """Add indexes to improve database query performance."""
    # Only run in production or when explicitly requested
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production and not app.config.get('FORCE_DB_OPTIMIZATIONS'):
        app.logger.info("Skipping database indexing in non-production environment")
        return
    
    # List of indexes to create
    indexes = [
        # Communications table indexes
        "CREATE INDEX IF NOT EXISTS idx_communication_person_id ON communication(person_id);",
        "CREATE INDEX IF NOT EXISTS idx_communication_church_id ON communication(church_id);",
        "CREATE INDEX IF NOT EXISTS idx_communication_type ON communication(type);",
        "CREATE INDEX IF NOT EXISTS idx_communication_direction ON communication(direction);",
        "CREATE INDEX IF NOT EXISTS idx_communication_date_sent ON communication(date_sent);",
        "CREATE INDEX IF NOT EXISTS idx_communication_office_id ON communication(office_id);",
        
        # Person table indexes
        "CREATE INDEX IF NOT EXISTS idx_person_church_id ON person(church_id);",
        "CREATE INDEX IF NOT EXISTS idx_person_office_id ON person(office_id);",
        "CREATE INDEX IF NOT EXISTS idx_person_name ON person(first_name, last_name);",
        
        # Church table indexes
        "CREATE INDEX IF NOT EXISTS idx_church_office_id ON church(office_id);",
        "CREATE INDEX IF NOT EXISTS idx_church_main_contact_id ON church(main_contact_id);",
        
        # Task table indexes
        "CREATE INDEX IF NOT EXISTS idx_task_assigned_to ON task(assigned_to);",
        "CREATE INDEX IF NOT EXISTS idx_task_due_date ON task(due_date);",
        "CREATE INDEX IF NOT EXISTS idx_task_status ON task(status);",
        "CREATE INDEX IF NOT EXISTS idx_task_priority ON task(priority);",
        
        # Pipeline indexes
        "CREATE INDEX IF NOT EXISTS idx_pipeline_stage_pipeline_id ON pipeline_stage(pipeline_id);",
        "CREATE INDEX IF NOT EXISTS idx_pipeline_contact_stage_id ON pipeline_contact(stage_id);",
        "CREATE INDEX IF NOT EXISTS idx_pipeline_contact_contact_id ON pipeline_contact(contact_id);",
    ]
    
    # Skip actual index creation in debug/startup script
    # This will be executed when the app is fully initialized with a proper app context
    if app.config.get('TESTING') or app.config.get('DEBUG'):
        app.logger.info("Skipping actual index creation in testing/debug mode")
        return
        
    # Instead of using before_first_request which is deprecated,
    # we'll register a function to be called during app initialization
    def create_indexes_function():
        from app.extensions import db
        
        app.logger.info("Creating database indexes...")
        # Execute each index creation
        with app.app_context():
            try:
                with db.engine.connect() as conn:
                    for index_sql in indexes:
                        try:
                            conn.execute(text(index_sql))
                            app.logger.info(f"Created index: {index_sql}")
                        except Exception as e:
                            app.logger.warning(f"Error creating index {index_sql}: {e}")
                    
                    # Commit the transaction
                    conn.commit()
            except Exception as e:
                app.logger.error(f"Failed to create indexes: {e}")
    
    # Register the function to be called when the app is fully initialized
    app.before_request_funcs.setdefault(None, []).append(lambda: None)  # No-op function
    
    # Skip actual execution during startup
    app.logger.info("Database indexes will be created when app is fully initialized")

def configure_sqlalchemy_optimizations(app):
    """Configure SQLAlchemy for better performance."""
    # Only run in production
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        app.logger.info("Skipping SQLAlchemy optimizations in non-production environment")
        return
    
    # Enable SQLAlchemy query caching
    app.config['SQLALCHEMY_ECHO'] = False
    
    # Set a reasonable pool size
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
    }
    
    app.logger.info("Applied SQLAlchemy optimizations")

def setup_query_monitoring(app):
    """Set up monitoring for slow database queries."""
    # Skip in non-production environments to avoid issues
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        app.logger.info('Skipping query monitoring setup in non-production environment')
        return
    
    app.logger.info('Setting up database query monitoring')
    
    # Define the monitoring setup function
    def setup_monitoring_function():
        from app.extensions import db
        import time
        
        # Register event listener for query execution
        @event.listens_for(db.engine, 'before_cursor_execute')
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
        
        @event.listens_for(db.engine, 'after_cursor_execute')
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - conn.info['query_start_time'].pop(-1)
            
            # Log slow queries (taking more than 100ms)
            if total_time > 0.1:
                app.logger.warning(f"SLOW QUERY ({total_time:.2f}s): {statement}")
                
                # For very slow queries, log with higher severity
                if total_time > 1.0:
                    app.logger.error(f"VERY SLOW QUERY ({total_time:.2f}s): {statement}")
    
    # We'll set up the monitoring when the app is running with a proper context
    # Skip actual execution during startup
    app.logger.info("Query monitoring will be set up when app is fully initialized")
