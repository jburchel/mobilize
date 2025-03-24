from functools import wraps
from flask import current_app, abort
from flask_login import current_user

def check_office_access(office_id):
    """Check if current user has access to the specified office."""
    if not current_user.is_authenticated:
        return False
    if current_user.is_super_admin():
        return True
    return current_user.office_id == office_id

def require_office_access(f):
    """Decorator to require office access for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        office_id = kwargs.get('office_id')
        if office_id and not check_office_access(office_id):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def require_super_admin(f):
    """Decorator to require super admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def require_office_admin(f):
    """Decorator to require office admin role for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

class OfficeDataFilter:
    """Filter querysets based on office visibility rules."""
    
    @staticmethod
    def filter_query(query, model):
        """Filter a query based on office visibility rules."""
        if not current_user.is_authenticated:
            return query.filter(False)  # Return empty query for unauthenticated users
            
        if current_user.is_super_admin():
            return query  # Super admins can see everything
            
        # For office-specific models
        if hasattr(model, 'office_id'):
            return query.filter(model.office_id == current_user.office_id)
            
        # For models with office relationship through contacts
        if hasattr(model, 'contact'):
            return query.join(model.contact).filter(model.contact.office_id == current_user.office_id)
            
        return query

    @staticmethod
    def can_access_record(record):
        """Check if current user can access a specific record."""
        if not current_user.is_authenticated:
            return False
            
        if current_user.is_super_admin():
            return True
            
        # Get office_id from record
        office_id = None
        if hasattr(record, 'office_id'):
            office_id = record.office_id
        elif hasattr(record, 'contact') and hasattr(record.contact, 'office_id'):
            office_id = record.contact.office_id
            
        return office_id == current_user.office_id

    @staticmethod
    def can_modify_record(record):
        """Check if current user can modify a specific record."""
        if not current_user.is_authenticated:
            return False
            
        if current_user.is_super_admin():
            return True
            
        # Office admins can modify any record in their office
        if current_user.is_admin():
            return OfficeDataFilter.can_access_record(record)
            
        # Regular users can only modify records they own
        return getattr(record, 'user_id', None) == current_user.id 