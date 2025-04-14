from datetime import datetime
from app.extensions import db
from app.models.base import Base
from google.oauth2.credentials import Credentials
import json
import os
from flask import current_app

class GoogleToken(Base):
    """Google OAuth token model for storing user tokens."""
    __tablename__ = 'google_tokens'

    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=True)
    token_type = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scopes = db.Column(db.Text, nullable=True)  # Store scopes as a JSON string
    email = db.Column(db.String, nullable=True)  # Store the user's Gmail address

    # Relationships
    user = db.relationship("User", back_populates="google_tokens")

    def __repr__(self):
        return f"<GoogleToken(user_id='{self.user_id}')>"

    def to_dict(self):
        """Convert token to dictionary."""
        return {
            'id': self.id,
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'user_id': self.user_id,
            'scopes': self.scopes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    def to_credentials(self):
        """Convert token to Google OAuth credentials object."""
        # Parse the scopes from JSON text if present, otherwise use default calendar scope
        token_scopes = ['https://www.googleapis.com/auth/calendar']
        if self.scopes:
            try:
                token_scopes = json.loads(self.scopes)
                current_app.logger.debug(f"Loaded token scopes: {token_scopes}")
            except:
                # If JSON parsing fails, use default scope
                current_app.logger.warning(f"Failed to parse token scopes, using default: {token_scopes}")
                pass
        
        # Check if client_id and client_secret are available
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            current_app.logger.error("GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in environment!")
            # Use dummy values for debugging - these won't work for actual auth
            client_id = client_id or "missing_client_id"
            client_secret = client_secret or "missing_client_secret"
                
        credentials = Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=token_scopes,
            expiry=self.expires_at
        )
        
        # Log credential status
        current_app.logger.debug(f"Created credentials for user {self.user_id}")
        current_app.logger.debug(f"Token expired: {credentials.expired}")
        current_app.logger.debug(f"Has refresh token: {'Yes' if self.refresh_token else 'No'}")
        
        return credentials 