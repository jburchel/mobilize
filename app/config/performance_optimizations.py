"""Performance optimizations for the Flask application in production."""

from flask import request
import time
import os
import psutil  # May need to be added to requirements.txt

def optimize_flask_app(app):
    """Apply performance optimizations to the Flask application.
    
    This function configures various performance optimizations for Flask
    in a production environment.
    """
    # Only apply optimizations in production
    # Check environment in a way compatible with newer Flask versions
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        return
    
    app.logger.info("Applying Flask performance optimizations for production")
    
    # Disable debug mode in production
    app.config['DEBUG'] = False
    
    # Enable Flask's built-in HTTP caching
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Increase maximum content length for uploads if needed
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    
    # Optimize for Cloud Run environment
    optimize_for_cloud_run(app)
    
    # Optimize memory usage
    optimize_memory_usage(app)
    
    # Register performance monitoring middleware
    register_performance_middleware(app)
    
    app.logger.info("Flask performance optimizations applied successfully")

def optimize_for_cloud_run(app):
    """Apply optimizations specific to Cloud Run environment."""
    # Check if we're running in Cloud Run
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    if not is_cloud_run:
        app.logger.info("Not running in Cloud Run, skipping Cloud Run optimizations")
        return
    
    app.logger.info("Applying Cloud Run specific optimizations")
    
    # Set appropriate worker configuration for gunicorn (if used)
    # These will be picked up by the gunicorn config
    os.environ['GUNICORN_WORKERS'] = '2'  # Use 2 workers per instance
    os.environ['GUNICORN_THREADS'] = '8'  # Use 8 threads per worker
    
    # Optimize for CPU-bound workloads
    os.environ['GUNICORN_WORKER_CLASS'] = 'gthread'
    
    # Set keep-alive for connection reuse
    os.environ['GUNICORN_KEEPALIVE'] = '65'  # 65 seconds keep-alive
    
    # Configure startup timeout to avoid cold start issues
    os.environ['GUNICORN_TIMEOUT'] = '60'  # 60 seconds timeout
    
    app.logger.info("Cloud Run optimizations applied")

def optimize_memory_usage(app):
    """Optimize memory usage to prevent OOM errors."""
    # Register a periodic memory check
    @app.before_request
    def check_memory_usage():
        try:
            # Only check every 100 requests to reduce overhead
            if getattr(app, '_request_count', 0) % 100 == 0:
                memory_info = psutil.Process(os.getpid()).memory_info()
                memory_usage_mb = memory_info.rss / 1024 / 1024
                
                # Log memory usage for monitoring
                if memory_usage_mb > 400:  # Over 400MB is concerning for a 512MB instance
                    app.logger.warning(f"High memory usage: {memory_usage_mb:.1f} MB")
                    
                # Update request counter
                app._request_count = getattr(app, '_request_count', 0) + 1
        except Exception as e:
            # Don't let memory checking crash the app
            app.logger.error(f"Error checking memory: {str(e)}")

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
            app.logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} took {duration:.2f}s"
            )
            
            # For very slow requests, log more details
            if duration > 2.0:
                app.logger.error(
                    f"VERY SLOW REQUEST: {request.method} {request.path} {request.args} took {duration:.2f}s"
                )
        
        # Add Server-Timing header for performance debugging
        response.headers['Server-Timing'] = f'total;dur={duration * 1000:.0f}'
        
        return response
