from app.extensions import db
from app.models.base import Base

class Role(Base):
    """Role model for managing user roles."""
    __tablename__ = 'roles'
    
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    permissions = db.relationship('RolePermission', back_populates='role', cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>" 