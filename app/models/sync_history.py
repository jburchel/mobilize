from datetime import datetime
from app.extensions import db

class SyncHistory(db.Model):
    """Model for tracking synchronization history with Google services."""
    __tablename__ = 'sync_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)  # contacts_sync, contacts_import, calendar_sync, email_sync
    status = db.Column(db.String(20), default='completed')  # completed, failed, partial
    items_processed = db.Column(db.Integer, default=0)
    items_created = db.Column(db.Integer, default=0)
    items_updated = db.Column(db.Integer, default=0)
    items_skipped = db.Column(db.Integer, default=0)
    items_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('sync_history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<SyncHistory {self.id}: {self.sync_type} - {self.status}>'
    
    @property
    def duration(self):
        """Calculate duration of sync operation in seconds."""
        if self.completed_at and self.created_at:
            return (self.completed_at - self.created_at).total_seconds()
        return None
    
    @property
    def formatted_duration(self):
        """Return a human-readable duration."""
        seconds = self.duration
        if seconds is None:
            return "In progress"
        
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s" 