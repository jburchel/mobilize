from datetime import datetime
from app import db
from app.models.base import BaseModel

class EmailSignature(BaseModel):
    """Email signature model for storing user email signatures."""
    __tablename__ = 'email_signatures'

    name = db.Column(db.String(100), nullable=False)  # Signature name (e.g., "Default", "Professional", "Personal")
    content = db.Column(db.Text, nullable=False)  # HTML content of the signature
    logo_url = db.Column(db.String, nullable=True)  # URL to the logo image
    is_default = db.Column(db.Boolean, default=False)  # Whether this is the default signature
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Reference to the user

    # Relationships
    user = db.relationship("User", back_populates="email_signatures")

    def __repr__(self):
        return f"<EmailSignature(name='{self.name}', user_id='{self.user_id}')>"

    def to_dict(self):
        """Convert email signature to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'logo_url': self.logo_url,
            'is_default': self.is_default,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 