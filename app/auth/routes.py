from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from firebase_admin import auth
from app.models.user import User
from app.extensions import db
from datetime import datetime, UTC
from app.auth.firebase import verify_firebase_token
from app.auth.google_oauth import get_google_auth_url, handle_oauth2_callback, create_oauth_flow, store_credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from app.models.google_token import GoogleToken
from google.oauth2 import id_token
from google.auth.transport import requests
import uuid
import os
from urllib.parse import urlencode

auth_bp = Blueprint('auth', __name__)

# Google OAuth2 scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# Google API configuration
CLIENT_SECRETS_FILE = os.environ.get('GOOGLE_CLIENT_SECRETS_FILE', 'client_secret.json')
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

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
        decoded_token = verify_firebase_token(id_token)
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get or create user
        user = User.query.filter_by(firebase_uid=decoded_token['uid']).first()
        
        if not user:
            # Create new user
            email_username = decoded_token.get('email').split('@')[0]
            user = User(
                email=decoded_token.get('email'),
                username=email_username,
                firebase_uid=decoded_token['uid'],
                first_name=decoded_token.get('name', '').split()[0] if decoded_token.get('name') else None,
                last_name=' '.join(decoded_token.get('name', '').split()[1:]) if decoded_token.get('name') else None,
                last_login=datetime.now(UTC),
                is_active=True,
                role='standard_user',
                office_id=1  # Default office ID
            )
            db.session.add(user)
            db.session.commit()
        else:
            # Update last login
            user.last_login = datetime.now(UTC)
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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # For GET requests, render the login template
    if request.method == 'GET':
        # If user is already logged in, redirect to dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return render_template('auth/login.html')
    
    # For POST requests, process login data (API)
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid credentials'}), 401
        
    # Update last login time
    user.last_login = datetime.now(UTC)
    db.session.commit()
    
    # Log the user in
    login_user(user)
    
    # Add office context to session
    session['office_id'] = user.office_id
    session['user_role'] = user.role
    session['office_admin'] = user.is_admin()
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'is_admin': user.is_admin(),
        'is_super_admin': user.is_super_admin(),
        'office_id': user.office_id
    })

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Handle user logout."""
    # Clear office context from session
    session.pop('office_id', None)
    session.pop('user_role', None)
    session.pop('office_admin', None)
    session.pop('user_id', None)  # Clear user_id added by Flask-Login
    
    logout_user()
    
    # For API requests (POST), return JSON response
    if request.method == 'POST':
        return jsonify({'message': 'Logout successful'})
    
    # For UI requests (GET), redirect to login page
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/google/auth')
@auth_bp.route('/google/authorize')
def google_auth():
    """Start Google OAuth2 flow."""
    auth_url = get_google_auth_url()
    return redirect(auth_url)

@auth_bp.route('/google/callback')
def oauth2callback():
    """Handle Google OAuth2 callback."""
    # Check for error parameter first - Google sends this when there's an auth problem
    error = request.args.get('error')
    if error:
        error_description = request.args.get('error_description', 'Unknown error')
        current_app.logger.error(f"Google OAuth error: {error} - {error_description}")
        flash(f'Google authentication error: {error_description}', 'danger')
        return redirect(url_for('auth.login'))
    
    # Create OAuth flow
    flow = create_oauth_flow()
    
    # Get user info from callback
    user_info, error = handle_oauth2_callback()
    if error:
        flash(f'Error during Google authentication: {error}', 'danger')
        return redirect(url_for('auth.login'))
    
    if not user_info:
        flash('Failed to get user info from Google', 'danger')
        return redirect(url_for('auth.login'))
    
    # Validate email domain for Crossover Global only in production
    email = user_info.get('email', '')
    
    # TEMPORARY: Bypass domain restriction for all users
    is_dev_mode = True
    
    if not email.endswith('@crossoverglobal.net') and not is_dev_mode:
        flash('Access is restricted to Crossover Global staff members with @crossoverglobal.net email addresses.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Log email being used
    current_app.logger.info(f"Login attempt with email: {email}")
    
    # Find or create user
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        # Generate a unique firebase_uid for Google OAuth users
        firebase_uid = f'google-oauth-{uuid.uuid4()}'
        email_username = user_info['email'].split('@')[0]
        user = User(
            email=user_info['email'],
            username=email_username,
            firebase_uid=firebase_uid,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            profile_image=user_info.get('picture', ''),
            role='standard_user',
            office_id=1  # Default office ID
        )
        db.session.add(user)
        db.session.commit()
    
    try:
        # Store credentials with the user's ID
        flow.fetch_token(authorization_response=request.url)
        store_credentials(flow.credentials, user.id)
        
        # Log in the user
        login_user(user)
        
        # Redirect to dashboard (which is at the root URL)
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        current_app.logger.error(f"Error in OAuth callback: {str(e)}")
        flash(f"Authentication error: {str(e)}", 'danger')
        return redirect(url_for('auth.login'))

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information."""
    return jsonify({
        'user': current_user.to_dict(),
        'is_admin': current_user.is_admin(),
        'is_super_admin': current_user.is_super_admin(),
        'office_id': current_user.office_id,
        'office': current_user.office.to_dict() if current_user.office else None
    })

@auth_bp.route('/dev-login')
def dev_login():
    """Development-only route for testing login functionality."""
    # Always allow dev login for testing purposes
    # Find or create a test user
    test_user = User.query.filter_by(email='test@example.com').first()
    if not test_user:
        test_user = User(
            email='test@example.com',
            username='testuser',
            firebase_uid='dev-test-user',
            first_name='Test',
            last_name='User',
            role='super_admin',  # Make the test user a super admin for full access
            office_id=1,  # Default office ID
            is_active=True
        )
        db.session.add(test_user)
        db.session.commit()
    
    # Log in the test user
    login_user(test_user)
    
    # Add office context to session
    session['office_id'] = test_user.office_id
    session['user_role'] = test_user.role
    session['office_admin'] = test_user.is_admin()
    
    # Redirect to dashboard
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/dev-login-standard')
def dev_login_standard():
    """Development-only route for testing login with standard user."""
    # Find or create a standard user (j.smith)
    standard_user = User.query.filter_by(email='j.smith@test.com').first()
    if not standard_user:
        standard_user = User(
            email='j.smith@test.com',
            username='jsmith',
            firebase_uid='dev-jsmith-user',
            first_name='John',
            last_name='Smith',
            role='standard_user',  # Standard user for testing non-admin features
            office_id=1,  # Default office ID
            is_active=True
        )
        # Set a password for form-based login
        standard_user.set_password('password123')
        db.session.add(standard_user)
        db.session.commit()
    
    # Log in as the standard user
    login_user(standard_user)
    
    # Add office context to session
    session['office_id'] = standard_user.office_id
    session['user_role'] = standard_user.role
    session['office_admin'] = standard_user.is_admin()
    
    # Redirect to dashboard
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/dev-login-office-admin')
def dev_login_office_admin():
    """Development-only route for testing login with office admin user."""
    # Find or create an office admin user
    admin_user = User.query.filter_by(email='admin@office.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@office.com',
            username='officeadmin',
            firebase_uid='dev-office-admin-user',
            first_name='Office',
            last_name='Admin',
            role='office_admin',  # Office admin for testing admin features
            office_id=1,  # Default office ID
            is_active=True
        )
        # Set a password for form-based login
        admin_user.set_password('password123')
        db.session.add(admin_user)
        db.session.commit()
    
    # Log in as the office admin user
    login_user(admin_user)
    
    # Add office context to session
    session['office_id'] = admin_user.office_id
    session['user_role'] = admin_user.role
    session['office_admin'] = admin_user.is_admin()
    
    # Redirect to dashboard
    return redirect(url_for('dashboard.index')) 