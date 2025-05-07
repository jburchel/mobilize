"""Middleware for logging user activities."""

import time
from functools import wraps
from flask import request, g, current_app
from flask_login import current_user
from app.utils.log_utils import log_activity

def get_client_ip():
    """Get the client IP address from the request."""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    else:
        return request.remote_addr

def log_request_activity():
    """Log information about the current request."""
    # Skip logging for static files and certain endpoints
    if ('/static/' in request.path or 
        '/favicon.ico' in request.path or
        '/health' in request.path):
        return
    
    # Get user information
    user = None
    if current_user and current_user.is_authenticated:
        user = {
            'name': current_user.name if hasattr(current_user, 'name') else current_user.username,
            'email': current_user.email if hasattr(current_user, 'email') else None
        }
    
    # Determine subsystem based on endpoint
    subsystem = 'API' if '/api/' in request.path else 'Web'
    
    # Determine operation based on HTTP method
    method_to_operation = {
        'GET': 'READ',
        'POST': 'CREATE',
        'PUT': 'UPDATE',
        'PATCH': 'UPDATE',
        'DELETE': 'DELETE'
    }
    operation = method_to_operation.get(request.method, request.method)
    
    # Create description
    description = f"Endpoint {request.path}"
    
    # Get client IP
    ip_address = get_client_ip()
    
    # Get request duration if available
    duration = None
    if hasattr(g, 'request_start_time'):
        duration = int((time.time() - g.request_start_time) * 1000)  # Convert to milliseconds
    
    # Determine status based on response code
    status = 'SUCCESS'
    if hasattr(g, 'response_status_code'):
        if g.response_status_code >= 400:
            status = 'FAILURE'
        elif g.response_status_code >= 300:
            status = 'WARNING'
    
    # Determine impact based on method and status
    impact = 'LOW'
    if operation in ['CREATE', 'UPDATE', 'DELETE']:
        impact = 'MEDIUM'
    if status == 'FAILURE':
        impact = 'HIGH'
    
    # Log the activity
    log_activity(
        subsystem=subsystem,
        operation=operation,
        description=description,
        status=status,
        impact=impact,
        user=user,
        ip_address=ip_address,
        resource_id=None,
        duration=duration
    )

class ActivityLoggerMiddleware:
    """Middleware for logging user activities."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with the Flask app."""
        @app.before_request
        def before_request():
            # Store the start time of the request
            g.request_start_time = time.time()
        
        @app.after_request
        def after_request(response):
            # Store the response status code
            g.response_status_code = response.status_code
            
            # Log the request activity
            try:
                log_request_activity()
            except Exception as e:
                current_app.logger.error(f"Error logging activity: {str(e)}")
            
            return response

def log_user_activity(subsystem, operation, description, impact='MEDIUM'):
    """Decorator for logging user activities in route handlers.
    
    Args:
        subsystem (str): The subsystem where the activity occurred
        operation (str): The operation performed
        description (str): A description of the activity
        impact (str): The impact level of the activity
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Get user information
            user = None
            if current_user and current_user.is_authenticated:
                user = {
                    'name': current_user.name if hasattr(current_user, 'name') else current_user.username,
                    'email': current_user.email if hasattr(current_user, 'email') else None
                }
            
            # Determine status based on response
            status = 'SUCCESS'
            if isinstance(result, tuple) and len(result) > 1 and isinstance(result[1], int):
                if result[1] >= 400:
                    status = 'FAILURE'
                elif result[1] >= 300:
                    status = 'WARNING'
            
            # Get client IP
            ip_address = get_client_ip()
            
            # Get resource ID if available in route parameters
            resource_id = None
            for key in ['id', 'user_id', 'contact_id', 'church_id', 'pipeline_id']:
                if key in kwargs:
                    resource_id = str(kwargs[key])
                    break
            
            # Log the activity
            log_activity(
                subsystem=subsystem,
                operation=operation,
                description=description,
                status=status,
                impact=impact,
                user=user,
                ip_address=ip_address,
                resource_id=resource_id,
                duration=duration
            )
            
            return result
        return decorated_function
    return decorator
