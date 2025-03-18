"""Module for setting up relationships between models."""
from app.extensions import db

def setup_relationships():
    """Set up relationships between models."""
    # Import models
    from app.models import Person, Church, Task, Communication, User, Office, EmailSignature, GoogleToken

    # Person relationships
    Person.church = db.relationship("Church", back_populates="people", foreign_keys="Person.church_id")
    Person.tasks = db.relationship("Task", back_populates="person")
    Person.communications = db.relationship("Communication", back_populates="person")
    Person.churches_main_contact = db.relationship("Church", back_populates="main_contact", foreign_keys="Church.main_contact_id")

    # Church relationships
    Church.main_contact = db.relationship("Person", back_populates="churches_main_contact", foreign_keys="Church.main_contact_id")
    Church.people = db.relationship("Person", back_populates="church", foreign_keys="Person.church_id")
    Church.tasks = db.relationship("Task", back_populates="church")
    Church.communications = db.relationship("Communication", back_populates="church")

    # Task relationships
    Task.person = db.relationship("Person", back_populates="tasks")
    Task.church = db.relationship("Church", back_populates="tasks")
    Task.assigned_user = db.relationship("User", back_populates="tasks")

    # Communication relationships
    Communication.person = db.relationship("Person", back_populates="communications")
    Communication.church = db.relationship("Church", back_populates="communications")
    Communication.sender = db.relationship("User", back_populates="communications")

    # User relationships
    User.tasks = db.relationship("Task", back_populates="assigned_user")
    User.communications = db.relationship("Communication", back_populates="sender")
    User.email_signatures = db.relationship("EmailSignature", back_populates="user")
    User.google_tokens = db.relationship("GoogleToken", back_populates="user")

    # Office relationships
    Office.contacts = db.relationship("Contact", back_populates="office") 