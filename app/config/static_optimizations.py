"""Static file optimizations for production environment."""

from flask import current_app, send_from_directory, request
import os
import gzip
import brotli
import time
from functools import wraps

def optimize_static_files(app):
    """Apply optimizations for static file serving in production."""
    # Set a deployment ID based on timestamp for cache versioning
    # This ensures static files are properly cached but updated on new deployments
    deployment_id = str(int(time.time()))
    app.config['DEPLOYMENT_ID'] = deployment_id
    app.logger.info(f"Setting deployment ID for static assets: {deployment_id}")
    
    # Skip advanced optimizations in non-production environment
    if app.config.get('FLASK_ENV') != 'production':
        app.logger.info("Skipping advanced static file optimizations in non-production environment")
        return

    # Configure Flask to serve static files with caching headers
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year in seconds
    
    # Add compression for static files
    @app.after_request
    def add_header(response):
        # Add caching headers for static files
        if 'Cache-Control' not in response.headers and request.path.startswith('/static'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
            response.headers['Expires'] = time.strftime(
                '%a, %d %b %Y %H:%M:%S GMT', 
                time.gmtime(time.time() + 31536000)
            )
        return response

    # Configure Flask-Talisman for security headers
    from flask_talisman import Talisman
    from flask import request  # Import request here to avoid circular imports
    
    csp = {
        'default-src': "'self'",
        'script-src': [
            "'self'", 
            "'unsafe-inline'", 
            "'unsafe-eval'", 
            "https://code.jquery.com",
            "https://cdn.jsdelivr.net",
            "https://www.googletagmanager.com",
            "https://www.google-analytics.com"
        ],
        'style-src': [
            "'self'", 
            "'unsafe-inline'", 
            "https://cdn.jsdelivr.net",
            "https://fonts.googleapis.com"
        ],
        'img-src': [
            "'self'", 
            "data:", 
            "https://www.google-analytics.com"
        ],
        'font-src': [
            "'self'", 
            "https://cdn.jsdelivr.net",
            "https://fonts.gstatic.com"
        ],
        'connect-src': [
            "'self'", 
            "https://www.google-analytics.com"
        ]
    }
    
    # Initialize Talisman with CSP
    Talisman(
        app,
        content_security_policy=csp,
        content_security_policy_nonce_in=['script-src', 'style-src'],
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_preload=True,
        session_cookie_secure=True,
        session_cookie_http_only=True
    )            
    
    current_app.logger.info("Applying static file optimizations for production")
    
    # Create compressed versions of static files
    precompress_static_files(app)
    
    # Override the static file serving function to use compressed files when available
    override_static_serving(app)
    
    current_app.logger.info("Static file optimizations applied successfully")

def precompress_static_files(app):
    """Pre-compress static files to gzip and brotli formats."""
    static_folder = os.path.join(app.root_path, 'static')
    
    # Skip if we've already compressed files
    if os.path.exists(os.path.join(static_folder, '.compressed')):
        return
    
    current_app.logger.info("Pre-compressing static files...")
    
    # File types to compress
    compressible_types = [
        '.css', '.js', '.html', '.xml', '.json', '.svg', '.txt', '.map'
    ]
    
    # Compress files
    for root, _, files in os.walk(static_folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Skip if not a compressible type
            if not any(filename.endswith(ext) for ext in compressible_types):
                continue
                
            # Skip if already compressed
            if filename.endswith('.gz') or filename.endswith('.br'):
                continue
                
            try:
                # Create gzip version
                with open(file_path, 'rb') as f_in:
                    with gzip.open(f"{file_path}.gz", 'wb', compresslevel=9) as f_out:
                        f_out.write(f_in.read())
                
                # Create brotli version
                with open(file_path, 'rb') as f_in:
                    compressed = brotli.compress(f_in.read(), quality=11)
                    with open(f"{file_path}.br", 'wb') as f_out:
                        f_out.write(compressed)
            except Exception as e:
                current_app.logger.error(f"Error compressing {file_path}: {str(e)}")
    
    # Create marker file to indicate compression is done
    with open(os.path.join(static_folder, '.compressed'), 'w') as f:
        f.write('1')
    
    current_app.logger.info("Static file compression complete")

def override_static_serving(app):
    """Override Flask's static file serving to use compressed versions when available."""
    original_send_static_file = app.send_static_file
    
    @wraps(original_send_static_file)
    def send_static_file_with_compression(filename):
        """Serve static files with compression support."""
        # Get accepted encodings from request
        from flask import request
        
        # Check if client accepts compression
        accept_encoding = request.headers.get('Accept-Encoding', '')
        
        static_folder = os.path.join(app.root_path, 'static')
        file_path = os.path.join(static_folder, filename)
        
        # Try brotli if supported
        if 'br' in accept_encoding and os.path.exists(f"{file_path}.br"):
            response = send_from_directory(
                app.static_folder, f"{filename}.br",
                mimetype=app.mimetypes.get(filename.split('.')[-1])
            )
            response.headers['Content-Encoding'] = 'br'
            return response
            
        # Try gzip if supported
        if 'gzip' in accept_encoding and os.path.exists(f"{file_path}.gz"):
            response = send_from_directory(
                app.static_folder, f"{filename}.gz",
                mimetype=app.mimetypes.get(filename.split('.')[-1])
            )
            response.headers['Content-Encoding'] = 'gzip'
            return response
            
        # Fall back to original
        return original_send_static_file(filename)
    
    # Replace the original function
    app.send_static_file = send_static_file_with_compression
