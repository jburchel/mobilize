from datetime import datetime
from app.extensions import db
from app.models.constants import PEOPLE_PIPELINE_CHOICES, CHURCH_PIPELINE_CHOICES
import enum

class PipelineType(str, enum.Enum):
    PEOPLE = 'person'
    CHURCHES = 'church'
    BOTH = 'both'

class Pipeline(db.Model):
    """Pipeline model for tracking contacts through different stages."""
    __tablename__ = 'pipelines'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    pipeline_type = db.Column(db.String(50), default='both')  # 'person', 'church', or 'both'
    office_id = db.Column(db.Integer, db.ForeignKey('offices.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Field to identify if this is a main/system pipeline
    is_main_pipeline = db.Column(db.Boolean, default=False)
    
    # Field to store which stage of the main pipeline this custom pipeline belongs to
    parent_pipeline_stage = db.Column(db.String(50), nullable=True)
    
    # Relationships
    office = db.relationship('Office', backref=db.backref('pipelines', lazy=True))
    stages = db.relationship('PipelineStage', back_populates='pipeline', lazy='dynamic', 
                           cascade='all, delete-orphan',
                           order_by='PipelineStage.order')
    pipeline_contacts = db.relationship('PipelineContact', back_populates='pipeline_parent', lazy='dynamic')
    
    def __repr__(self):
        return f'<Pipeline {self.name}>'
        
    def get_active_stages(self):
        """Get all active stages for this pipeline ordered by position."""
        return self.stages.order_by(PipelineStage.order).all()
        
    def count_contacts(self):
        """Count contacts in this pipeline."""
        # Use a direct SQL query to get an accurate count
        from sqlalchemy import text
        from app.extensions import db
        
        try:
            # Use direct SQL for most reliable results
            result = db.session.execute(
                text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
                {"pipeline_id": self.id}
            )
            count = result.scalar() or 0
            
            # Return the count without logging to stderr which can cause BrokenPipeError
            return count
        except Exception:
            # Silently handle the error without writing to stderr
            # This prevents BrokenPipeError when the pipe is closed
            return 0
        
    def contact_count(self):
        """Alias for count_contacts() method."""
        return self.count_contacts()
        
    def get_available_parent_stages(self):
        """Get available parent pipeline stages based on pipeline type."""
        if self.pipeline_type == 'people' or self.pipeline_type == 'person':
            return [choice[0] for choice in PEOPLE_PIPELINE_CHOICES]
        elif self.pipeline_type == 'church':
            return [choice[0] for choice in CHURCH_PIPELINE_CHOICES]
        return []

    def to_dict(self):
        """Convert object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'pipeline_type': self.pipeline_type,
            'office_id': self.office_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contact_count': self.count_contacts()
        }
        
    @classmethod
    def get_main_pipeline(cls, pipeline_type):
        """Get the main pipeline for the given type."""
        return cls.query.filter_by(is_main_pipeline=True, pipeline_type=pipeline_type).first()
        
    def get_first_stage(self):
        """Get the first stage of the pipeline."""
        return self.stages.order_by(PipelineStage.order).first()


class PipelineStage(db.Model):
    """Model representing a stage in a pipeline."""
    __tablename__ = 'pipeline_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), default='#3498db')  # Default blue color
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Automation fields
    auto_move_days = db.Column(db.Integer, nullable=True)
    auto_reminder = db.Column(db.Boolean, default=False)
    auto_task_template = db.Column(db.Text, nullable=True)
    
    # Relationships
    pipeline = db.relationship('Pipeline', back_populates='stages')
    contacts_in_stage = db.relationship('PipelineContact', back_populates='current_stage')
    from_stage_history = db.relationship('PipelineStageHistory',
                              foreign_keys='PipelineStageHistory.from_stage_id', lazy='dynamic',
                              back_populates='from_stage')
    to_stage_history = db.relationship('PipelineStageHistory',
                              foreign_keys='PipelineStageHistory.to_stage_id', lazy='dynamic',
                              back_populates='to_stage')
    
    def __repr__(self):
        return f'<PipelineStage {self.name} (Pipeline: {self.pipeline_id})>'
        
    def to_dict(self):
        """Convert object to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'order': self.order,
            'color': self.color,
            'pipeline_id': self.pipeline_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'contact_count': self.contacts_in_stage.count(),
            'auto_move_days': self.auto_move_days,
            'auto_reminder': self.auto_reminder,
            'auto_task_template': self.auto_task_template
        }


class PipelineContact(db.Model):
    """Model representing a contact in a pipeline."""
    __tablename__ = 'pipeline_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=False)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False)
    current_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'), nullable=False)
    entered_at = db.Column(db.DateTime, default=datetime.now)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    contact = db.relationship('Contact', backref='pipeline_contacts')
    pipeline_parent = db.relationship('Pipeline', back_populates='pipeline_contacts')
    current_stage = db.relationship('PipelineStage', back_populates='contacts_in_stage')
    stage_history = db.relationship('PipelineStageHistory', back_populates='pipeline_contact',
                             cascade='all, delete-orphan', passive_deletes=True)
    
    def __repr__(self):
        return f'<PipelineContact {self.contact_id} in Pipeline {self.pipeline_id}>'
        
    def move_to_stage(self, stage_id, user_id=None, notes=None):
        """Move contact to a new stage and create history record."""
        try:
            previous_stage_id = self.current_stage_id
            from flask import current_app
            from app.models.person import Person
            from app.models.church import Church
            
            current_app.logger.info(f"Moving contact {self.contact_id} from stage {previous_stage_id} to {stage_id}")
            
            # Get the new stage name to update the contact's pipeline_stage field
            new_stage = PipelineStage.query.get(stage_id)
            if not new_stage:
                current_app.logger.error(f"Stage {stage_id} not found")
                return False
            
            # Create history record
            if previous_stage_id != stage_id:
                history_entry = PipelineStageHistory(
                    pipeline_contact_id=self.id,
                    from_stage_id=previous_stage_id,
                    to_stage_id=stage_id,
                    created_by_id=user_id,
                    notes=notes,
                    created_at=datetime.now()
                )
                db.session.add(history_entry)
                # Commit the history record first
                db.session.commit()
                current_app.logger.info(f"Created history entry for contact {self.contact_id} move")
            
            # Update current stage in PipelineContact
            self.current_stage_id = stage_id
            self.last_updated = datetime.now()
            
            # Update the pipeline_stage field in the Contact model (Person or Church)
            contact = None
            # Check if this is a Person contact
            contact = Person.query.get(self.contact_id)
            if contact:
                current_app.logger.info(f"Updating Person {self.contact_id} pipeline_stage to {new_stage.name}")
                contact.pipeline_stage = new_stage.name
            else:
                # Check if this is a Church contact
                contact = Church.query.get(self.contact_id)
                if contact:
                    current_app.logger.info(f"Updating Church {self.contact_id} pipeline_stage to {new_stage.name}")
                    contact.pipeline_stage = new_stage.name
                else:
                    current_app.logger.warning(f"Could not find contact {self.contact_id} in Person or Church tables")
            
            # Commit all changes
            db.session.commit()
            current_app.logger.info(f"Successfully updated contact {self.contact_id} stage to {stage_id} in database")
            
            return True
        except Exception as e:
            db.session.rollback()
            import traceback
            traceback.print_exc()
            from flask import current_app
            current_app.logger.error(f"Error moving contact to stage: {str(e)}")
            return False
    
    def to_dict(self):
        """Convert object to dictionary."""
        contact_dict = self.contact.to_dict() if self.contact else {}
        stage_dict = self.current_stage.to_dict() if self.current_stage else {}
        
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'pipeline_id': self.pipeline_id,
            'current_stage_id': self.current_stage_id,
            'entered_at': self.entered_at.isoformat() if self.entered_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'contact': contact_dict,
            'stage': stage_dict
        }


class PipelineStageHistory(db.Model):
    """Model for tracking movement of contacts between pipeline stages."""
    __tablename__ = 'pipeline_stage_history'
    
    id = db.Column(db.Integer, primary_key=True)
    pipeline_contact_id = db.Column(db.Integer, db.ForeignKey('pipeline_contacts.id', ondelete='CASCADE'))
    from_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'))
    to_stage_id = db.Column(db.Integer, db.ForeignKey('pipeline_stages.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pipeline_contact = db.relationship('PipelineContact', back_populates='stage_history')
    from_stage = db.relationship('PipelineStage', 
                               foreign_keys=[from_stage_id],
                               back_populates='from_stage_history')
    to_stage = db.relationship('PipelineStage',
                             foreign_keys=[to_stage_id],
                             back_populates='to_stage_history')
    user = db.relationship('User', backref='pipeline_stage_history')
    
    def __repr__(self):
        return f'<PipelineStageHistory {self.id}: {self.from_stage_id} -> {self.to_stage_id}>'
        
    def to_dict(self):
        """Convert object to dictionary."""
        from_stage_name = self.from_stage.name if self.from_stage else "New Entry"
        to_stage_name = self.to_stage.name if self.to_stage else "Unknown"
        
        return {
            'id': self.id,
            'pipeline_contact_id': self.pipeline_contact_id,
            'from_stage_id': self.from_stage_id,
            'to_stage_id': self.to_stage_id,
            'from_stage': from_stage_name,
            'to_stage': to_stage_name,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by_id': self.created_by_id,
            'created_by': self.user.name if self.user else None
        } 