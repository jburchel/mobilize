from datetime import datetime, UTC
from app.extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.models.constants import PEOPLE_PIPELINE_CHOICES, CHURCH_PIPELINE_CHOICES

class Pipeline(db.Model):
    """Pipeline model represents a workflow for managing contacts through stages."""
    __tablename__ = 'pipelines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    pipeline_type = db.Column(db.String(20), default='people')  # Type: 'people' or 'church'
    description = db.Column(db.Text)
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Field to identify if this is a main/system pipeline
    is_main_pipeline = db.Column(db.Boolean, default=False)
    
    # Field to store which stage of the main pipeline this custom pipeline belongs to
    parent_pipeline_stage = db.Column(db.String(50), nullable=True)
    
    # Relationships
    office = db.relationship('Office', backref=db.backref('pipelines', lazy='dynamic'))
    stages = db.relationship('PipelineStage', backref='pipeline', lazy='dynamic', 
                            order_by='PipelineStage.order')
    pipeline_contacts = db.relationship('PipelineContact', backref='pipeline', lazy='dynamic')
    
    def __repr__(self):
        return f'<Pipeline {self.name}>'
        
    def get_active_stages(self):
        """Get all active stages for this pipeline ordered by sequence."""
        return self.stages.filter_by(is_active=True).order_by(PipelineStage.order).all()
        
    def contact_count(self):
        """Get count of contacts in this pipeline."""
        return self.pipeline_contacts.count()
        
    def get_available_parent_stages(self):
        """Get available parent pipeline stages based on pipeline type."""
        if self.pipeline_type == 'people':
            return [choice[0] for choice in PEOPLE_PIPELINE_CHOICES]
        elif self.pipeline_type == 'church':
            return [choice[0] for choice in CHURCH_PIPELINE_CHOICES]
        return []

    def to_dict(self):
        """Convert pipeline to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'pipeline_type': self.pipeline_type,
            'description': self.description,
            'office_id': self.office_id,
            'is_active': self.is_active,
            'is_main_pipeline': self.is_main_pipeline,
            'parent_pipeline_stage': self.parent_pipeline_stage,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'stages': [stage.to_dict() for stage in self.stages]
        }
        
    @classmethod
    def get_main_pipeline(cls, pipeline_type):
        """Get the main pipeline for the given type."""
        return cls.query.filter_by(is_main_pipeline=True, pipeline_type=pipeline_type).first()
        
    def get_first_stage(self):
        """Get the first stage of the pipeline."""
        return self.stages.order_by(PipelineStage.order).first()


class PipelineStage(db.Model):
    """PipelineStage model represents a stage in a pipeline."""
    __tablename__ = 'pipeline_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default="#3498db")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Automation fields
    auto_move_days = db.Column(db.Integer, nullable=True)
    auto_reminder = db.Column(db.Boolean, default=False)
    auto_task_template = db.Column(db.Text, nullable=True)
    
    # Relationships
    contacts_in_stage = db.relationship('PipelineContact', 
                                      foreign_keys='PipelineContact.current_stage_id',
                                      backref='current_stage', lazy='dynamic')
    
    from_stage_history = db.relationship('PipelineStageHistory',
                                        foreign_keys='PipelineStageHistory.from_stage_id',
                                        backref='from_stage', lazy='dynamic')
                                    
    to_stage_history = db.relationship('PipelineStageHistory',
                                      foreign_keys='PipelineStageHistory.to_stage_id',
                                      backref='to_stage', lazy='dynamic')
    
    def __repr__(self):
        return f'<PipelineStage {self.name} (Pipeline: {self.pipeline_id})>'
        
    def contact_count(self):
        """Get count of contacts in this stage."""
        return self.contacts_in_stage.count()
        
    def to_dict(self):
        """Convert pipeline stage to dictionary."""
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'name': self.name,
            'description': self.description,
            'order': self.order,
            'color': self.color,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'auto_move_days': self.auto_move_days,
            'auto_reminder': self.auto_reminder,
            'auto_task_template': self.auto_task_template
        }


class PipelineContact(db.Model):
    """PipelineContact model represents a contact in a pipeline at a specific stage."""
    __tablename__ = 'pipeline_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    current_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'), nullable=False)
    entered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    contact = db.relationship('Contact', backref=db.backref('pipeline_memberships', lazy='dynamic'))
    stage_history = db.relationship('PipelineStageHistory', 
                                  backref='pipeline_contact', lazy='dynamic',
                                  order_by='PipelineStageHistory.moved_at.desc()')
    
    def __repr__(self):
        return f'<PipelineContact {self.contact_id} in Pipeline {self.pipeline_id}>'
        
    def move_to_stage(self, stage_id, user_id=None, notes=None, is_automated=False):
        """Move contact to a new stage and create history record."""
        previous_stage_id = self.current_stage_id
        
        # Create history record
        history = PipelineStageHistory(
            pipeline_contact_id=self.id,
            from_stage_id=previous_stage_id,
            to_stage_id=stage_id,
            moved_at=datetime.utcnow(),
            moved_by_user_id=user_id,
            notes=notes,
            is_automated=is_automated
        )
        db.session.add(history)
        
        # Update current stage
        self.current_stage_id = stage_id
        self.last_updated = datetime.utcnow()
        
        # Update the contact's main pipeline stage if this is not a main pipeline
        self.sync_with_main_pipeline()
        
        db.session.commit()
        return history
    
    def sync_with_main_pipeline(self):
        """
        Sync the contact's main pipeline fields with this pipeline's stage.
        This ensures that Person.people_pipeline and Person.pipeline_stage
        or Church.church_pipeline fields stay in sync with custom pipelines.
        """
        from app.models import Person, Church
        
        # Skip if this is already a main pipeline
        if self.pipeline.is_main_pipeline:
            return
            
        # Get the contact
        contact = self.contact
        
        # Get the stage
        stage = PipelineStage.query.get(self.current_stage_id)
        if not stage:
            return
            
        # Get the parent pipeline stage
        parent_stage = self.pipeline.parent_pipeline_stage
        if not parent_stage:
            return
            
        # Update the appropriate fields based on contact type
        if contact.type == 'person':
            person = Person.query.get(contact.id)
            if person:
                person.people_pipeline = parent_stage
                person.pipeline_stage = stage.name
                
        elif contact.type == 'church':
            church = Church.query.get(contact.id)
            if church:
                church.church_pipeline = parent_stage
                
        db.session.add(contact)
        
    def to_dict(self):
        """Convert pipeline contact to dictionary."""
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'pipeline_id': self.pipeline_id,
            'current_stage_id': self.current_stage_id,
            'entered_at': self.entered_at.isoformat() if self.entered_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class PipelineStageHistory(db.Model):
    """PipelineStageHistory model tracks movement of contacts between pipeline stages."""
    __tablename__ = 'pipeline_stage_history'
    
    id = db.Column(db.Integer, primary_key=True)
    pipeline_contact_id = db.Column(db.Integer, db.ForeignKey('pipeline_contacts.id'), nullable=False)
    from_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'), nullable=True)
    to_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'), nullable=False)
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)
    moved_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text)
    is_automated = db.Column(db.Boolean, default=False)
    
    # Relationships
    moved_by_user = db.relationship('User', backref=db.backref('pipeline_stage_movements', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PipelineStageHistory {self.id}: {self.from_stage_id} -> {self.to_stage_id}>'
        
    def to_dict(self):
        """Convert pipeline stage history to dictionary."""
        return {
            'id': self.id,
            'pipeline_contact_id': self.pipeline_contact_id,
            'from_stage_id': self.from_stage_id,
            'to_stage_id': self.to_stage_id,
            'moved_at': self.moved_at.isoformat() if self.moved_at else None,
            'moved_by_user_id': self.moved_by_user_id,
            'notes': self.notes,
            'is_automated': self.is_automated
        } 