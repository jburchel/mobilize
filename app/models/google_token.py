from datetime import datetime
from app import db
from app.models.base import BaseModel

class GoogleToken(BaseModel):
    """Google OAuth token model for storing user tokens."""
    __tablename__ = 'google_tokens'

    access_token = db.Column(db.String, nullable=False)
    refresh_token = db.Column(db.String, nullable=True)
    token_type = db.Column(db.String, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 