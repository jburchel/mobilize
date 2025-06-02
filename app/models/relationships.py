"""Module for setting up relationships between models."""
from app.extensions import db
import inspect
from sqlalchemy import and_, or_

def setup_relationships():
    """Set up relationships between models."""
    # Import models
    from app.models import Person, Church, Task, Communication, User, Office, EmailSignature, GoogleToken, Contact, Pipeline, PipelineStage, PipelineContact, PipelineStageHistory
    
    # Define all relationships
    relationships = [
        # Person relationships
        (Person, "church", db.relationship("Church", back_populates="people", foreign_keys="Person.church_id", overlaps="people")),
        (Person, "tasks", db.relationship("Task", back_populates="person", overlaps="person,tasks")),
        (Person, "communications", db.relationship("Communication", back_populates="person", overlaps="person,communications")),
        (Person, "churches_main_contact", db.relationship("Church", back_populates="main_contact", foreign_keys="Church.main_contact_id", overlaps="main_contact")),
        (Person, "pipeline_contacts", db.relationship("PipelineContact", back_populates="person", overlaps="person,pipeline_contacts")),

        # Church relationships
        (Church, "main_contact", db.relationship("Person", back_populates="churches_main_contact", foreign_keys="Church.main_contact_id", overlaps="churches_main_contact")),
        (Church, "people", db.relationship("Person", back_populates="church", foreign_keys="Person.church_id", overlaps="church")),
        (Church, "tasks", db.relationship("Task", back_populates="church", overlaps="church,tasks")),
        (Church, "communications", db.relationship("Communication", back_populates="church", overlaps="church,communications")),
        (Church, "owner", db.relationship("User", back_populates="owned_churches", foreign_keys="[Church.owner_id]", overlaps="owned_churches")),
        (Church, "office", db.relationship("Office", back_populates="churches", overlaps="churches")),

        # Task relationships
        (Task, "person", db.relationship("Person", back_populates="tasks", overlaps="tasks,person")),
        (Task, "church", db.relationship("Church", back_populates="tasks", overlaps="tasks,church")),
        (Task, "assigned_to_user", db.relationship("User", back_populates="assigned_tasks", foreign_keys="Task.assigned_to", overlaps="assigned_tasks")),
        (Task, "owner", db.relationship("User", back_populates="owned_tasks", foreign_keys="Task.owner_id", overlaps="owned_tasks")),
        (Task, "created_by_user", db.relationship("User", back_populates="created_tasks", foreign_keys="Task.created_by", overlaps="created_tasks")),
        (Task, "office", db.relationship("Office", back_populates="tasks", overlaps="tasks")),

        # Communication relationships
        (Communication, "person", db.relationship("Person", back_populates="communications", overlaps="communications,person")),
        (Communication, "church", db.relationship("Church", back_populates="communications", overlaps="communications,church")),
        (Communication, "sender", db.relationship("User", back_populates="communications", overlaps="communications,sender", foreign_keys="Communication.user_id")),
        (Communication, "owner", db.relationship("User", back_populates="owned_communications", overlaps="owned_communications,owner", foreign_keys="Communication.owner_id")),
        (Communication, "office", db.relationship("Office", back_populates="communications", overlaps="communications,office", foreign_keys="Communication.office_id")),

        # Pipeline relationships
        (Pipeline, "stages", db.relationship("PipelineStage", back_populates="pipeline", cascade="all, delete-orphan", overlaps="pipeline,stages")),
        (Pipeline, "contacts", db.relationship("PipelineContact", back_populates="pipeline", cascade="all, delete-orphan", overlaps="pipeline,contacts")),
        (PipelineStage, "pipeline", db.relationship("Pipeline", back_populates="stages", overlaps="stages,pipeline")),
        (PipelineStage, "contacts", db.relationship("PipelineContact", back_populates="stage", overlaps="stage,contacts")),
        (PipelineContact, "pipeline", db.relationship("Pipeline", back_populates="contacts", overlaps="contacts,pipeline")),
        (PipelineContact, "stage", db.relationship("PipelineStage", back_populates="contacts", overlaps="contacts,stage")),
        (PipelineContact, "person", db.relationship("Person", back_populates="pipeline_contacts", overlaps="pipeline_contacts,person")),
        (PipelineContact, "history", db.relationship("PipelineStageHistory", back_populates="pipeline_contact", cascade="all, delete-orphan", overlaps="pipeline_contact,history")),
        (PipelineStageHistory, "pipeline_contact", db.relationship("PipelineContact", back_populates="history", overlaps="history,pipeline_contact")),

        # User relationships
        (User, "communications", db.relationship("Communication", back_populates="sender", overlaps="sender,communications,userSender", foreign_keys="Communication.user_id")),
        (User, "owned_communications", db.relationship("Communication", back_populates="owner", overlaps="owner,owned_communications", foreign_keys="Communication.owner_id")),
        (User, "email_signatures", db.relationship("EmailSignature", back_populates="user", overlaps="user")),
        (User, "google_tokens", db.relationship("GoogleToken", back_populates="user", overlaps="user")),
        (User, "contacts", db.relationship("Contact", back_populates="user", foreign_keys="Contact.user_id", overlaps="user,contacts")),
        (User, "owned_churches", db.relationship("Church", back_populates="owner", foreign_keys="[Church.owner_id]", overlaps="owner,owned_churches")),
        (User, "assigned_tasks", db.relationship("Task", back_populates="assigned_to_user", foreign_keys="Task.assigned_to", overlaps="assigned_to_user,assigned_tasks")),
        (User, "owned_tasks", db.relationship("Task", back_populates="owner", foreign_keys="Task.owner_id", overlaps="owner,owned_tasks")),
        (User, "created_tasks", db.relationship("Task", back_populates="created_by_user", foreign_keys="Task.created_by", overlaps="created_by_user,created_tasks")),

        # Office relationships
        (Office, "contacts", db.relationship("Contact", back_populates="office", overlaps="office,contacts")),
        (Office, "communications", db.relationship("Communication", back_populates="office", overlaps="office,communications", foreign_keys="Communication.office_id")),
        (Office, "churches", db.relationship("Church", back_populates="office", overlaps="office")),
        (Office, "tasks", db.relationship("Task", back_populates="office", overlaps="office,assigned_tasks")),
    ]
    
    # Apply all relationships
    for cls, name, rel in relationships:
        if not hasattr(cls, name):
            setattr(cls, name, rel) 