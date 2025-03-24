"""Module for setting up relationships between models."""
from app.extensions import db
import inspect
from sqlalchemy import and_, or_

def setup_relationships():
    """Set up relationships between models."""
    # Import models
    from app.models import Person, Church, Task, Communication, User, Office, EmailSignature, GoogleToken, Contact
    
    # Define all relationships
    relationships = [
        # Person relationships
        (Person, "church", db.relationship("Church", back_populates="people", foreign_keys="Person.church_id", overlaps="people")),
        (Person, "tasks", db.relationship("Task", back_populates="person", overlaps="person,tasks", foreign_keys="Task.person_id")),
        (Person, "communications", db.relationship("Communication", back_populates="person", overlaps="person,communications")),
        (Person, "churches_main_contact", db.relationship("Church", back_populates="main_contact", foreign_keys="Church.main_contact_id", overlaps="main_contact")),
        
        # Church relationships
        (Church, "main_contact", db.relationship("Person", back_populates="churches_main_contact", foreign_keys="Church.main_contact_id", overlaps="churches_main_contact")),
        (Church, "people", db.relationship("Person", back_populates="church", foreign_keys="Person.church_id", overlaps="church")),
        (Church, "tasks", db.relationship("Task", back_populates="church", overlaps="church,tasks", foreign_keys="Task.church_id")),
        (Church, "communications", db.relationship("Communication", back_populates="church", overlaps="church,communications")),
        (Church, "owner", db.relationship("User", back_populates="owned_churches", foreign_keys="[Church.owner_id]", overlaps="owned_churches")),
        
        # Task relationships
        (Task, "person", db.relationship("Person", back_populates="tasks", overlaps="tasks,person", foreign_keys="Task.person_id")),
        (Task, "church", db.relationship("Church", back_populates="tasks", overlaps="tasks,church", foreign_keys="Task.church_id")),
        (Task, "assigned_user", db.relationship("User", overlaps="tasks", primaryjoin="foreign(Task.assigned_to) == User.id")),
        (Task, "owner", db.relationship("User", back_populates="owned_tasks", overlaps="owned_tasks,owner", foreign_keys="Task.owner_id")),
        
        # Communication relationships
        (Communication, "person", db.relationship("Person", back_populates="communications", overlaps="communications,person")),
        (Communication, "church", db.relationship("Church", back_populates="communications", overlaps="communications,church")),
        (Communication, "sender", db.relationship("User", back_populates="communications", overlaps="communications,sender", foreign_keys="Communication.user_id")),
        (Communication, "owner", db.relationship("User", back_populates="owned_communications", overlaps="owned_communications,owner", foreign_keys="Communication.owner_id")),
        (Communication, "office", db.relationship("Office", back_populates="communications", overlaps="communications,office", foreign_keys="Communication.office_id")),
        
        # User relationships
        (User, "tasks", db.relationship("Task", overlaps="assigned_user", primaryjoin="User.id == foreign(Task.assigned_to)")),
        (User, "owned_tasks", db.relationship("Task", back_populates="owner", overlaps="owner,owned_tasks", foreign_keys="Task.owner_id")),
        (User, "communications", db.relationship("Communication", back_populates="sender", overlaps="sender,communications", foreign_keys="Communication.user_id")),
        (User, "owned_communications", db.relationship("Communication", back_populates="owner", overlaps="owner,owned_communications", foreign_keys="Communication.owner_id")),
        (User, "email_signatures", db.relationship("EmailSignature", back_populates="user", overlaps="user")),
        (User, "google_tokens", db.relationship("GoogleToken", back_populates="user", overlaps="user")),
        (User, "contacts", db.relationship("Contact", back_populates="user", foreign_keys="Contact.user_id", overlaps="user,contacts")),
        (User, "owned_churches", db.relationship("Church", back_populates="owner", foreign_keys="[Church.owner_id]", overlaps="owner,owned_churches")),
        
        # Office relationships
        (Office, "contacts", db.relationship("Contact", back_populates="office", overlaps="office,contacts")),
        (Office, "communications", db.relationship("Communication", back_populates="office", overlaps="office,communications", foreign_keys="Communication.office_id"))
    ]
    
    # Apply all relationships
    for cls, name, rel in relationships:
        if not hasattr(cls, name):
            setattr(cls, name, rel) 