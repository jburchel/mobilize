from app import db
from app.models.base import BaseModel

class Permission(BaseModel):
    """Permission model for managing user permissions."""
    __tablename__ = 'permissions'
    
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>" 