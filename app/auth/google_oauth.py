from flask import current_app, url_for, session, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timezone, timedelta

# OAuth 2.0 scopes for various Google services we'll use
SCOPES = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/contacts.other.readonly'
]

def get_oauth_redirect_uri():
    """
    Get the OAuth redirect URI, handling various environments properly.
    
    This function handles redirect URIs for different environments:
    - Cloud Run
    - Custom domains
    - Local development
    """
    # Get the host from the request headers
    host = request.headers.get('Host', '')
    scheme = request.headers.get('X-Forwarded-Proto', 'https')
    
    # Log the host and scheme for debugging
    current_app.logger.info(f"OAuth Redirect - Host: {host}, Scheme: {scheme}")
    
    # Check if we're running on Cloud Run
    if 'run.app' in host:
        redirect_uri = f"https://{host}/api/auth/google/callback"
        current_app.logger.info(f"Using Cloud Run redirect URI: {redirect_uri}")
        return redirect_uri
    
    # For production with custom domain or local development, use the BASE_URL from environment variables
    base_url = os.environ.get('BASE_URL') or current_app.config.get('BASE_URL')
    if base_url:
        # Ensure HTTPS for production
        if os.environ.get('FLASK_ENV') == 'production' and not base_url.startswith('https://'):
            base_url = base_url.replace('http://', 'https://')
        redirect_uri = f"{base_url}/api/auth/google/callback"
        current_app.logger.info(f"Using BASE_URL redirect URI: {redirect_uri}")
        return redirect_uri
    
    # Fallback to Flask's url_for
    redirect_uri = url_for('auth.oauth2callback', _external=True)
    current_app.logger.info(f"Using fallback redirect URI: {redirect_uri}")
    return redirect_uri

def create_oauth_flow():
    """Create a Google OAuth2 flow instance."""
    # Ensure HTTPS is required in production
    if os.environ.get('FLASK_ENV') == 'production':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '0'
    else:
        # Allow HTTP in development
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        
    # Get the proper redirect URI that works with ngrok
    redirect_uri = get_oauth_redirect_uri()
    
    client_config = {
        "web": {
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    # Print the redirect URI for debugging
    current_app.logger.debug(f"Using redirect URI: {redirect_uri}")
    
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES
    )
    
    flow.redirect_uri = redirect_uri
    return flow

def get_google_auth_url():
    """Get the Google OAuth2 authorization URL."""
    flow = create_oauth_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to ensure refresh_token
    )
    session['state'] = state
    
    # Print the auth URL for debugging
    current_app.logger.debug(f"Auth URL: {auth_url}")
    
    return auth_url

def handle_oauth2_callback():
    """Handle the OAuth2 callback from Google."""
    state = session.get('state')
    if not state or state != request.args.get('state'):
        return None, "Invalid state parameter"
    
    try:
        flow = create_oauth_flow()
        # Ensure we're using HTTPS for the authorization response
        authorization_response = request.url
        if authorization_response.startswith('http:') and 'run.app' in authorization_response:
            authorization_response = authorization_response.replace('http:', 'https:', 1)
        
        flow.fetch_token(
            authorization_response=authorization_response
        )
        credentials = flow.credentials
        
        # Store credentials in the database
        store_credentials(credentials)
        
        # Get user info
        user_info = get_user_info(credentials)
        return user_info, None
    except Exception as e:
        return None, str(e)

def store_credentials(credentials, user_id=None):
    """Store Google OAuth credentials in the database."""
    from app.config.database import db
    from app.models.google_token import GoogleToken
    from flask_login import current_user
    
    # Use provided user_id or fall back to current_user.id
    user_id = user_id or current_user.id
    
    # Log credential details for debugging - remove sensitive info
    current_app.logger.debug(f"Credentials received - has token: {'Yes' if hasattr(credentials, 'token') else 'No'}")
    current_app.logger.debug(f"Credentials received - has refresh_token: {'Yes' if hasattr(credentials, 'refresh_token') else 'No'}")
    current_app.logger.debug(f"Credentials received - has expiry: {'Yes' if hasattr(credentials, 'expiry') else 'No'}")
    current_app.logger.debug(f"Credentials received - has scopes: {'Yes' if hasattr(credentials, 'scopes') else 'No'}")
    
    # Get token attributes with safety checks
    token = getattr(credentials, 'token', None)
    refresh_token = getattr(credentials, 'refresh_token', None)
    token_type = getattr(credentials, 'token_type', 'Bearer')  # Default to Bearer
    expiry = getattr(credentials, 'expiry', datetime.now(timezone.utc) + timedelta(hours=1))
    
    # Convert scopes list to JSON string for storage
    scopes = getattr(credentials, 'scopes', SCOPES)
    scopes_json = json.dumps(scopes) if scopes else json.dumps(SCOPES)
    
    # Get the user's email from their profile
    user_email = None
    try:
        user_info = get_user_info(credentials)
        if user_info and 'email' in user_info:
            user_email = user_info['email']
            current_app.logger.info(f"Got user email: {user_email}")
    except Exception as e:
        current_app.logger.error(f"Error getting user email: {str(e)}")
    
    if not user_email:
        current_app.logger.error("CRITICAL: Failed to get user email from profile!")
        
    # For debugging - check if user_info contains expected fields
    if user_info:
        current_app.logger.info(f"USER INFO FIELDS: {', '.join(user_info.keys())}")
    
    # Update or create token record
    token_record = GoogleToken.query.filter_by(user_id=user_id).first()
    
    if token_record:
        # Update existing token
        token_record.access_token = token
        # Only update refresh_token if we got a new one (Google doesn't always return it)
        if refresh_token:
            token_record.refresh_token = refresh_token
        token_record.token_type = token_type
        token_record.expires_at = expiry
        token_record.scopes = scopes_json
        if user_email:
            token_record.email = user_email
            current_app.logger.info(f"Updated email to {user_email} for user {user_id}")
    else:
        # Create new token record
        token_record = GoogleToken(
            user_id=user_id,
            access_token=token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_at=expiry,
            scopes=scopes_json,
            email=user_email
        )
        db.session.add(token_record)
        current_app.logger.info(f"Created new token record with email {user_email} for user {user_id}")
    
    db.session.commit()
    current_app.logger.info(f"Stored/updated Google credentials for user {user_id}")
    return token_record

def get_user_info(credentials):
    """Get Google user information using OAuth2 credentials."""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        return user_info
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {str(e)}")
        return None

def get_google_credentials(user_id):
    """Retrieve and refresh Google OAuth credentials if necessary."""
    from app.models.google_token import GoogleToken
    from app.config.database import db
    
    token = GoogleToken.query.filter_by(user_id=user_id).first()
    if not token:
        return None

    # Handle token scopes - use stored scopes if available, otherwise use default SCOPES
    token_scopes = SCOPES
    if token.scopes:
        try:
            token_scopes = json.loads(token.scopes)
        except Exception as e:
            # If JSON loading fails, use default scopes
            current_app.logger.warning(f"Failed to parse token scopes: {str(e)}")
            pass

    credentials = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=token_scopes
    )
    
    if credentials.expired:
        try:
            credentials.refresh(Request())
            # Update stored token
            token.access_token = credentials.token
            token.expires_at = credentials.expiry
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Error refreshing token: {str(e)}")
            return None
            
    return credentials 