from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role in ['super_admin', 'office_admin']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def office_required(f):
    """Decorator to require user to have an office assignment."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not hasattr(current_user, 'office_id') or not current_user.office_id:
            abort(403)
        # Set current_office_id if not already set
        if not hasattr(current_user, 'current_office_id'):
            current_user.current_office_id = current_user.office_id
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    """Decorator to require super admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'super_admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function 