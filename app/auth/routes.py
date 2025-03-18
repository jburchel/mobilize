from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from firebase_admin import auth
from app.models.user import User
from app import db
from datetime import datetime
from app.auth.firebase import verify_firebase_token
from app.auth.google_oauth import get_google_auth_url, handle_oauth2_callback, create_oauth_flow, store_credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from app.models.google_token import GoogleToken
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid

auth_bp = Blueprint('auth', __name__)

# Google OAuth2 scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

def get_google_user_info(credentials):
    """Get user info from Google using OAuth2 credentials."""
    try:
        # Get ID token from credentials
        request = requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request, current_app.config['GOOGLE_CLIENT_ID']
        )
        
        return {
            'email': id_info['email'],
            'given_name': id_info.get('given_name', ''),
            'family_name': id_info.get('family_name', ''),
        }
    except Exception as e:
        current_app.logger.error(f'Error getting Google user info: {str(e)}')
        return None

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """Verify Firebase ID token and return user info."""
    try:
        # Get the ID token from the request
        id_token = request.json.get('idToken')
        if not id_token:
            return jsonify({'error': 'No token provided'}), 401

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        
        # Get or create user
        user = User.query.filter_by(firebase_uid=decoded_token['uid']).first()
        
        if not user:
            # Create new user
            user = User(
                email=decoded_token.get('email'),
                firebase_uid=decoded_token['uid'],
                first_name=decoded_token.get('name', '').split()[0] if decoded_token.get('name') else None,
                last_name=' '.join(decoded_token.get('name', '').split()[1:]) if decoded_token.get('name') else None,
                last_login=datetime.utcnow(),
                is_active=True,
                role='standard_user'
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()

        return jsonify({
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error in verify_token: {str(e)}")
        return jsonify({'error': 'Invalid token'}), 401

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle Firebase login and create/update user."""
    try:
        # Get the ID token from the request
        id_token = request.json.get('idToken')
        if not id_token:
            return jsonify({'error': 'No ID token provided'}), 400

        # Verify the Firebase token
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401

        # Get or create user
        user = User.query.filter_by(firebase_uid=decoded_token['uid']).first()
        if not user:
            user = User(
                email=decoded_token['email'],
                firebase_uid=decoded_token['uid'],
                first_name=decoded_token.get('name', '').split()[0] if decoded_token.get('name') else '',
                last_name=decoded_token.get('name', '').split()[-1] if decoded_token.get('name') else '',
                profile_picture_url=decoded_token.get('picture', '')
            )
            db.session.add(user)
            db.session.commit()

        # Log in the user
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'needsGoogleAuth': user.google_refresh_token is None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Handle user logout."""
    try:
        # Clear Google OAuth tokens if they exist
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        if token:
            db.session.delete(token)
            db.session.commit()
        
        # Log out the user
        logout_user()
        
        # Clear session
        session.clear()
        
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f"Error during logout: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_bp.route('/google/auth')
@auth_bp.route('/google/authorize')
def google_auth():
    """Start Google OAuth2 flow."""
    auth_url = get_google_auth_url()
    return redirect(auth_url)

@auth_bp.route('/google/callback')
def oauth2callback():
    """Handle Google OAuth2 callback."""
    # Create OAuth flow
    flow = create_oauth_flow()
    
    # Get user info from callback
    user_info, error = handle_oauth2_callback()
    if error:
        flash(f'Error during Google authentication: {error}', 'error')
        return redirect(url_for('auth.login'))
    
    if not user_info:
        flash('Failed to get user info from Google', 'error')
        return redirect(url_for('auth.login'))
    
    # Find or create user
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Generate a unique firebase_uid for Google OAuth users
        firebase_uid = f'google-oauth-{uuid.uuid4()}'
        user = User(
            email=user_info['email'],
            firebase_uid=firebase_uid,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            profile_picture_url=user_info.get('picture', ''),
            role='standard_user'
        )
        db.session.add(user)
        db.session.commit()
    
    # Store credentials with the user's ID
    flow.fetch_token(authorization_response=request.url)
    store_credentials(flow.credentials, user.id)
    
    # Log in the user
    login_user(user)
    
    # Redirect to dashboard
    return redirect('/dashboard')

@auth_bp.route('/user')
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify(current_user.to_dict()) 