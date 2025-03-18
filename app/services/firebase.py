import os
import logging
from functools import wraps
from flask import current_app, request, g
import firebase_admin
from firebase_admin import credentials, auth

logger = logging.getLogger(__name__)

def init_firebase(app):
    """Initialize Firebase Admin SDK.
    
    For now, this is a placeholder that logs a warning if Firebase credentials are missing.
    """
    required_fields = ['private_key_id', 'private_key', 'client_email']
    missing_fields = [field for field in required_fields if not os.environ.get(f'FIREBASE_{field.upper()}')]
    
    if missing_fields:
        logger.warning(f"Firebase authentication disabled. Missing required fields: {', '.join(missing_fields)}")
        return None
    
    # TODO: Implement actual Firebase initialization when credentials are available
    return None

def verify_firebase_token(f):
    """Decorator to verify Firebase ID token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('FIREBASE_ENABLED', False):
            logger.warning("Firebase authentication bypassed - Firebase is disabled")
            return f(*args, **kwargs)
            
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {'message': 'No token provided'}, 401
            
        token = auth_header.split('Bearer ')[1]
        try:
            decoded_token = auth.verify_id_token(token)
            g.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            return {'message': 'Invalid token'}, 401
            
    return decorated_function 