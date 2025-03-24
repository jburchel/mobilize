"""Models package."""
from app.extensions import db, Base

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()

# Import all models
from .user import User
from .contact import Contact
from .person import Person
from .church import Church
from .task import Task
from .communication import Communication
from .office import Office
from .permission import Permission
from .google_token import GoogleToken
from .email_signature import EmailSignature
from .sync_history import SyncHistory
from .pipeline import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory

# Make them available at the package level
__all__ = [
    'db',
    'Base',
    'User',
    'Contact',
    'Person',
    'Church',
    'Task',
    'Communication',
    'Office',
    'Permission',
    'GoogleToken',
    'EmailSignature',
    'SyncHistory',
    'Pipeline',
    'PipelineStage',
    'PipelineContact',
    'PipelineStageHistory'
] 