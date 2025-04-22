import firebase_admin
from firebase_admin import credentials, auth
from flask import current_app
from functools import wraps
from flask import request, jsonify
import os
import logging
import json

def init_firebase(app):
    """Initialize Firebase Admin SDK."""
    logger = app.logger
    
    logger.info("Starting Firebase initialization...")
    
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        logger.info("Firebase already initialized")
    except ValueError:
        # First check for a consolidated credentials JSON
        firebase_creds_json = os.getenv('FIREBASE_CREDENTIALS')
        if firebase_creds_json:
            try:
                logger.info("Using consolidated FIREBASE_CREDENTIALS env var")
                # Parse the JSON credentials
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully from consolidated credentials")
                return
            except Exception as e:
                logger.error(f"Error initializing Firebase from consolidated credentials: {str(e)}")
                # Continue to try individual credentials
        
        # Check if required environment variables are set for individual creds
        required_vars = [
            'FIREBASE_PRIVATE_KEY_ID',
            'FIREBASE_PRIVATE_KEY',
            'FIREBASE_CLIENT_EMAIL',
            'FIREBASE_CLIENT_ID',
            'FIREBASE_CLIENT_CERT_URL',
            'FIREBASE_PROJECT_ID'
        ]
        
        # Log all environment variables for debugging
        for var in required_vars:
            if os.getenv(var):
                if var != 'FIREBASE_PRIVATE_KEY':
                    logger.info(f"Found {var}: {os.getenv(var)[:10]}...")
                else:
                    logger.info(f"Found {var}: [REDACTED]")
            else:
                logger.warning(f"Missing {var}")
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            logger.warning(f"Missing Firebase environment variables: {', '.join(missing_vars)}")
            logger.warning("Firebase authentication will be disabled")
            return
        
        try:
            # Get project_id from environment
            project_id = os.getenv('FIREBASE_PROJECT_ID')
            logger.info(f"Using Firebase project ID: {project_id}")
            
            # Initialize Firebase with configuration from environment
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                "private_key": os.getenv('FIREBASE_PRIVATE_KEY', '').replace('\\n', '\n'),
                "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
            })
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized successfully from individual credentials")
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            logger.warning("Firebase authentication will be disabled")

def verify_firebase_token(id_token):
    """Verify the Firebase ID token."""
    try:
        # Check if Firebase is initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            current_app.logger.warning("Firebase not initialized. Token verification will fail.")
            return None

        # Convert bytes to string if necessary
        if isinstance(id_token, bytes):
            id_token = id_token.decode('utf-8')

        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        current_app.logger.error(f"Error verifying Firebase token: {str(e)}")
        return None

def auth_required(f):
    """Decorator to require Firebase authentication for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = verify_firebase_token(id_token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Add the user's Firebase UID to the request context
        request.firebase_uid = decoded_token['uid']
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin role for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = verify_firebase_token(id_token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Check if user has admin custom claim
        if not decoded_token.get('admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        request.firebase_uid = decoded_token['uid']
        return f(*args, **kwargs)
    
    return decorated_function 