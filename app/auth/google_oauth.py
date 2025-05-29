from flask import url_for, session, request, current_app
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
    - Production (Cloud Run with custom domain or standard Cloud Run URL)
    - Local development (optionally with BASE_URL for ngrok/custom local setups)
    """
    # With ProxyFix, request.scheme and request.host should be reliable.
    # X-Forwarded-Proto and Host headers are used by ProxyFix to set these.
    
    flask_env = os.environ.get('FLASK_ENV', 'development')
    
    if flask_env == 'production':
        # In production, always use the scheme and host from the request,
        # which ProxyFix should have set correctly based on X-Forwarded headers.
        # This handles both '.run.app' domains and custom domains like 'mobilize-crm.org'.
        scheme = request.scheme # Should be 'https' on Cloud Run
        host = request.host     # Should be 'mobilize-crm.org' or '*.run.app'
        redirect_uri = f"{scheme}://{host}/api/auth/google/callback"
        current_app.logger.info(f"[PROD] Using redirect URI from request.scheme and request.host: {redirect_uri}")
        return redirect_uri
    else: # Development or other environments
        current_app.logger.info(f"[DEV/OTHER] FLASK_ENV is '{flask_env}'. Checking for BASE_URL.")
        # For local development, allow BASE_URL from environment or config for ngrok/custom setups
        base_url = os.environ.get('BASE_URL') or current_app.config.get('BASE_URL')
        if base_url:
            # Ensure scheme is present, default to http if not specified for local dev
            if not base_url.startswith(('http://', 'https://')):
                base_url = f"http://{base_url}"
            redirect_uri = f"{base_url}/api/auth/google/callback"
            current_app.logger.info(f"[DEV/OTHER] Using BASE_URL redirect URI: {redirect_uri}")
            return redirect_uri
        
        # Fallback to Flask's url_for for local development if no BASE_URL
        # This will typically generate http://localhost:port or http://127.0.0.1:port
        try:
            redirect_uri = url_for('auth.oauth2callback', _external=True)
            current_app.logger.info(f"[DEV/OTHER] Using fallback redirect URI from url_for: {redirect_uri}")
            return redirect_uri
        except RuntimeError as e:
            # This can happen if url_for is called outside of a request context or SERVER_NAME is not set
            current_app.logger.error(f"[DEV/OTHER] RuntimeError generating redirect_uri with url_for: {e}. Defaulting to hardcoded localhost.")
            # As a last resort for development, if url_for fails (e.g. no request context during setup)
            return "http://localhost:8000/api/auth/google/callback"

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
    
    # Log the auth URL for debugging
    if current_app:
        current_app.logger.debug(f"Auth URL: {auth_url}")
    else:
        print(f"Auth URL: {auth_url}")
    
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