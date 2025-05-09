"""Frontend performance optimizations for the Flask application."""

from flask import request  # current_app removed as unused
import os

def optimize_frontend_performance(app):
    """Apply frontend performance optimizations.
    
    This function configures various optimizations for frontend assets
    to improve application loading and rendering speed.
    """
    # Temporarily disable all optimizations for fresh deployment
    app.logger.info("Frontend optimizations DISABLED for fresh deployment")
    return
    
    # Only apply optimizations in production
    is_production = app.config.get('ENV') == 'production' or app.config.get('FLASK_ENV') == 'production'
    if not is_production:
        app.logger.info("Skipping frontend optimizations in non-production environment")
        return
        
    app.logger.info("Applying frontend performance optimizations")
    
    # Configure cache headers for static assets
    configure_static_cache(app)
    
    # Enable compression for responses
    configure_response_compression(app)
    
    app.logger.info("Frontend performance optimizations applied successfully")

def configure_static_cache(app):
    """Configure cache headers for static assets."""
    # Set long cache times for static assets
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Add cache-control headers for different asset types
    @app.after_request
    def add_cache_headers(response):
        # Only add cache headers for GET requests to static assets
        if request.method == 'GET' and '/static/' in request.path:
            # Different cache policies based on file type
            if request.path.endswith(('.css', '.js')):
                # Long cache for CSS and JS files
                response.headers['Cache-Control'] = 'public, max-age=31536000'
            elif request.path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico')):
                # Even longer cache for images
                response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
            else:
                # Default cache policy for other static files
                response.headers['Cache-Control'] = 'public, max-age=86400'
                
        return response

def configure_response_compression(app):
    """Configure response compression for text-based content."""
    try:
        from flask_compress import Compress
        compress = Compress()
        compress.init_app(app)
        app.logger.info("Response compression enabled")
    except ImportError:
        app.logger.warning("flask_compress not installed, skipping response compression")
        # Add to requirements.txt for next deployment
        requirements_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'requirements.txt')
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                requirements = f.read()
            if 'flask-compress' not in requirements:
                with open(requirements_path, 'a') as f:
                    f.write('\nflask-compress==1.13')  # Add the latest version
                app.logger.info("Added flask-compress to requirements.txt")
