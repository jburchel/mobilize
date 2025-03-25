from datetime import datetime
import json
from app.extensions import db
from app.models.base import Base


class EmailTemplate(Base):
    """Email template model for storing reusable email templates."""
    __tablename__ = 'email_templates'

    name = db.Column(db.String(100), nullable=False)  # Template name
    subject = db.Column(db.String(255), nullable=False)  # Email subject line
    content = db.Column(db.Text, nullable=False)  # HTML content of the template
    category = db.Column(db.String(50), nullable=True)  # Category for organization
    variables = db.Column(db.Text, nullable=True)  # JSON-encoded list of template variables
    is_active = db.Column(db.Boolean, default=True)  # Whether this template is active
    
    # Foreign keys
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Reference to the user
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)  # Office this template belongs to
    
    # Relationships
    user = db.relationship("User", foreign_keys=[created_by], backref="created_templates")
    office = db.relationship("Office", backref="email_templates")

    def __repr__(self):
        return f"<EmailTemplate(name='{self.name}', id='{self.id}')>"
    
    def get_variables(self):
        """Get template variables as a list."""
        if self.variables:
            try:
                return json.loads(self.variables)
            except:
                return []
        return []
    
    def set_variables(self, variables_list):
        """Set template variables from a list."""
        if variables_list:
            self.variables = json.dumps(variables_list)
        else:
            self.variables = None
    
    def to_dict(self):
        """Convert email template to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject,
            'content': self.content,
            'category': self.category,
            'variables': self.get_variables(),
            'is_active': self.is_active,
            'created_by': self.created_by,
            'office_id': self.office_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 