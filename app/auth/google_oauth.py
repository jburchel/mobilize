from flask import current_app, url_for, session, redirect, request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json

# OAuth 2.0 scopes for various Google services we'll use
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/contacts'
]

def create_oauth_flow():
    """Create a Google OAuth2 flow instance."""
    client_config = {
        "web": {
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [url_for('auth.oauth2callback', _external=True)]
        }
    }
    
    flow = Flow.from_client_config(
        client_config=client_config,
        scopes=SCOPES
    )
    
    flow.redirect_uri = url_for('auth.oauth2callback', _external=True)
    return flow

def get_google_auth_url():
    """Get the Google OAuth2 authorization URL."""
    flow = create_oauth_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return auth_url

def handle_oauth2_callback():
    """Handle the OAuth2 callback from Google."""
    state = session.get('state')
    if not state or state != request.args.get('state'):
        return None, "Invalid state parameter"
    
    try:
        flow = create_oauth_flow()
        flow.fetch_token(
            authorization_response=request.url
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
    
    # Convert credentials to dict for storage
    creds_dict = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }
    
    # Update or create token record
    token = GoogleToken.query.filter_by(user_id=user_id).first()
    if token:
        token.access_token = credentials.token
        token.refresh_token = credentials.refresh_token
        token.token_type = credentials.token_type
        token.expires_at = credentials.expiry
        token.scopes = credentials.scopes
    else:
        token = GoogleToken(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_type=credentials.token_type,
            expires_at=credentials.expiry,
            scopes=credentials.scopes
        )
        db.session.add(token)
    
    db.session.commit()

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
        
    credentials = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        scopes=token.scopes
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