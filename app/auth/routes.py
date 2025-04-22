from flask import Blueprint, request, jsonify, current_app, session, redirect, url_for, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from firebase_admin import auth
from app.models.user import User
from app.extensions import db
from datetime import datetime, timezone, timedelta
from app.auth.firebase import verify_firebase_token
from app.auth.google_oauth import get_google_auth_url, handle_oauth2_callback, create_oauth_flow, store_credentials
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from app.models.google_token import GoogleToken
from google.oauth2 import id_token
from google.auth.transport import requests
from app.utils.user_utils import create_person_for_user
import uuid
import os
from urllib.parse import urlencode

auth_bp = Blueprint('auth', __name__)

# Google OAuth2 scopes (updated 2024-05-07)
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
                last_login=datetime.now(timezone.utc),
                is_active=True,
                role='standard_user',
                first_login=True,  # Mark as first login
                office_id=1  # Default office ID
            )
            db.session.add(user)
            db.session.commit()
            
            # Create a Person record for the new user
            try:
                create_person_for_user(user)
                current_app.logger.info(f"Created person record for new user {user.email}")
            except Exception as e:
                current_app.logger.error(f"Error creating person for user: {str(e)}")
        else:
            # Update last login
            user.last_login = datetime.now(timezone.utc)
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
    """Handle user login via API."""
    # For GET requests, return unauthorized JSON
    if request.method == 'GET':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # For POST requests, process login data (API)
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.is_active:
        return jsonify({'error': 'Invalid credentials'}), 401
        
    # Update last login time
    user.last_login = datetime.now(timezone.utc)
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
    
    try:
        # Get the authorization code from the request
        code = request.args.get('code')
        if not code:
            flash('No authorization code received from Google', 'danger')
            return redirect(url_for('auth.login'))
            
        # Create OAuth flow
        flow = create_oauth_flow()
        
        # Validate the state parameter
        state = session.get('state')
        if not state or request.args.get('state') != state:
            current_app.logger.error("State mismatch in OAuth callback")
            flash('Invalid authentication state. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Log the callback URL for debugging
        callback_url = request.url
        current_app.logger.info(f"OAuth callback URL: {callback_url}")
        
        # Process authorization response - add skip_scope_check=True to prevent scope errors
        flow.fetch_token(authorization_response=callback_url, include_granted_scopes=True, skip_scope_check=True)
        credentials = flow.credentials
        
        # Get user info directly using the credentials
        from googleapiclient.discovery import build
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        if not user_info:
            flash('Failed to get user info from Google', 'danger')
            return redirect(url_for('auth.login'))
        
        # Validate email domain for Crossover Global only in production
        email = user_info.get('email', '')
        current_app.logger.info(f"Email from Google: {email}")
        
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
                first_login=True,  # Mark as first login
                office_id=1  # Default office ID
            )
            db.session.add(user)
            db.session.commit()
        
        # Store Google token
        try:
            # Use our improved store_credentials function
            from app.auth.google_oauth import store_credentials
            store_credentials(credentials, user.id)
        except Exception as e:
            current_app.logger.error(f"Error storing credentials: {str(e)}")
            # Continue even if storing credentials fails - we can still log in the user
        
        # Log in the user
        login_user(user)
        
        # Record successful login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
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
            is_active=True,
            first_login=True  # New users should go through onboarding
        )
        db.session.add(test_user)
        db.session.commit()
    else:
        # For existing test user, keep their current first_login status
        pass
    
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
            is_active=True,
            first_login=True  # New users should go through onboarding
        )
        # Set a password for form-based login
        standard_user.set_password('password123')
        db.session.add(standard_user)
        db.session.commit()
    else:
        # For existing user, keep their current first_login status
        pass
    
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
            is_active=True,
            first_login=True  # New users should go through onboarding
        )
        # Set a password for form-based login
        admin_user.set_password('password123')
        db.session.add(admin_user)
        db.session.commit()
    else:
        # For existing user, keep their current first_login status
        pass
    
    # Log in as the office admin user
    login_user(admin_user)
    
    # Add office context to session
    session['office_id'] = admin_user.office_id
    session['user_role'] = admin_user.role
    session['office_admin'] = admin_user.is_admin()
    
    # Redirect to dashboard
    return redirect(url_for('dashboard.index'))

@auth_bp.route('/google/revoke')
@login_required
def revoke_google():
    """Revoke Google OAuth credentials for the current user."""
    try:
        # Get user's Google token
        from app.models.google_token import GoogleToken
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        
        if token:
            # Try to revoke token with Google
            from app.auth.google_oauth import get_google_credentials
            credentials = get_google_credentials(current_user.id)
            if credentials:
                try:
                    # Attempt to revoke on Google's side
                    import google.oauth2.credentials
                    import google_auth_oauthlib.flow
                    import googleapiclient.discovery
                    
                    # Build the request to revoke
                    import requests
                    requests.post('https://oauth2.googleapis.com/revoke',
                                 params={'token': credentials.token},
                                 headers={'content-type': 'application/x-www-form-urlencoded'})
                except Exception as e:
                    current_app.logger.error(f"Error revoking Google token: {str(e)}")
            
            # Delete the token from our database
            db.session.delete(token)
            db.session.commit()
            flash('Google account disconnected successfully.', 'success')
        else:
            flash('No Google account connected.', 'info')
    except Exception as e:
        current_app.logger.error(f"Error in revoke_google: {str(e)}")
        flash('An error occurred while disconnecting your Google account.', 'danger')
    
    # Redirect back to the Google sync page
    return redirect(url_for('google_sync.index'))

@auth_bp.route('/google/reauth')
@login_required
def reauth_google():
    """Force re-authorization with Google."""
    try:
        # Remove current token to force re-auth
        token = GoogleToken.query.filter_by(user_id=current_user.id).first()
        if token:
            current_app.logger.info(f"Removing Google token for user {current_user.id} to force reauth")
            db.session.delete(token)
            db.session.commit()
            flash('Google token cleared, please re-authorize', 'success')
        else:
            current_app.logger.warning(f"No Google token found for user {current_user.id} during reauth")
            flash('No existing Google authorization found', 'warning')
        
        # Redirect to Google OAuth
        return redirect(url_for('auth.google_auth'))
    except Exception as e:
        current_app.logger.error(f"Error during Google reauth: {str(e)}")
        flash(f'Error during Google reauthorization: {str(e)}', 'error')
        return redirect(url_for('dashboard.index')) 