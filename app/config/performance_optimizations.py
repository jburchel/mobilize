"""Performance optimizations for the Flask application in production."""

from flask import current_app, request
import time

def optimize_flask_app(app):
    """Apply performance optimizations to the Flask application.
    
    This function configures various performance optimizations for Flask
    in a production environment.
    """
    # Only apply optimizations in production
    if app.config['ENV'] != 'production':
        return
    
    current_app.logger.info("Applying Flask performance optimizations for production")
    
    # Disable debug mode in production
    app.config['DEBUG'] = False
    
    # Enable Flask's built-in HTTP caching
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Increase maximum content length for uploads if needed
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    
    # Register performance monitoring middleware
    register_performance_middleware(app)
    
    current_app.logger.info("Flask performance optimizations applied successfully")

def register_performance_middleware(app):
    """Register middleware for performance monitoring."""
    @app.before_request
    def before_request():
        # Store the start time for this request
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # Skip for static files to reduce log noise
        if request.path.startswith('/static/'):
            return response
        
        # Calculate request duration
        duration = time.time() - request.start_time
        
        # Log slow requests (more than 500ms)
        if duration > 0.5:
            current_app.logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}s"
            )
        
        # Add Server-Timing header for performance debugging
        response.headers['Server-Timing'] = f'total;dur={duration * 1000:.0f}'
        
        return response
