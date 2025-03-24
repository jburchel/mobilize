"""
Script to migrate existing contacts to the main pipelines.
This is used to ensure all Person and Church objects are associated with
the correct stage in the main pipeline based on their existing pipeline fields.
"""
import logging
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church
from app.models.contact import Contact
from app.extensions import db
from datetime import datetime
from flask import current_app

logger = logging.getLogger('migration')

def migrate_contacts_to_main_pipelines():
    """Migrate existing contacts to the main pipelines based on their type."""
    from app.models import Contact, Pipeline, PipelineContact, PipelineStage, PipelineStageHistory
    from app.extensions import db
    from flask import current_app
    
    try:
        # Get the main pipelines
        people_main_pipeline = Pipeline.get_main_pipeline('people')
        church_main_pipeline = Pipeline.get_main_pipeline('church')
        
        if not people_main_pipeline or not church_main_pipeline:
            current_app.logger.warning("Main pipelines not found. Migration skipped.")
            return
        
        # Get the first stage for each pipeline
        people_first_stage = people_main_pipeline.get_first_stage()
        church_first_stage = church_main_pipeline.get_first_stage()
        
        if not people_first_stage or not church_first_stage:
            current_app.logger.warning("Pipeline stages not found. Migration skipped.")
            return
        
        # Get contacts not already in the main pipelines
        people_in_pipeline = db.session.query(Contact.id).join(
            PipelineContact, PipelineContact.contact_id == Contact.id
        ).filter(
            PipelineContact.pipeline_id == people_main_pipeline.id,
            Contact.type == 'person'
        ).subquery()
        
        churches_in_pipeline = db.session.query(Contact.id).join(
            PipelineContact, PipelineContact.contact_id == Contact.id
        ).filter(
            PipelineContact.pipeline_id == church_main_pipeline.id,
            Contact.type == 'church'
        ).subquery()
        
        # Find people contacts not in the pipeline
        people_to_add = Contact.query.filter(
            Contact.type == 'person',
            Contact.id.notin_(people_in_pipeline)
        ).all()
        
        # Find church contacts not in the pipeline
        churches_to_add = Contact.query.filter(
            Contact.type == 'church',
            Contact.id.notin_(churches_in_pipeline)
        ).all()
        
        # Add people to the people pipeline
        for person in people_to_add:
            pipeline_contact = PipelineContact(
                pipeline_id=people_main_pipeline.id,
                contact_id=person.id,
                current_stage_id=people_first_stage.id
            )
            db.session.add(pipeline_contact)
            
            # Create initial stage history
            history = PipelineStageHistory(
                pipeline_contact=pipeline_contact,
                to_stage_id=people_first_stage.id,
                notes="Initial stage (automatic migration)"
            )
            db.session.add(history)
        
        # Add churches to the church pipeline
        for church in churches_to_add:
            pipeline_contact = PipelineContact(
                pipeline_id=church_main_pipeline.id,
                contact_id=church.id,
                current_stage_id=church_first_stage.id
            )
            db.session.add(pipeline_contact)
            
            # Create initial stage history
            history = PipelineStageHistory(
                pipeline_contact=pipeline_contact,
                to_stage_id=church_first_stage.id,
                notes="Initial stage (automatic migration)"
            )
            db.session.add(history)
        
        db.session.commit()
        
        current_app.logger.info(f"Migrated {len(people_to_add)} people and {len(churches_to_add)} churches to main pipelines.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error migrating contacts to main pipelines: {str(e)}")
        # Don't re-raise the exception to prevent app startup failure

def migrate_people(people_pipeline, people_stages):
    """Migrate all people to the main people pipeline."""
    print("Migrating people to main pipeline...")
    
    # Get all people
    all_people = Person.query.all()
    count = 0
    
    for person in all_people:
        # Skip if already in the pipeline
        existing = PipelineContact.query.filter_by(
            pipeline_id=people_pipeline.id,
            contact_id=person.id
        ).first()
        
        if existing:
            continue
            
        # Get the appropriate stage based on people_pipeline value
        stage_name = person.people_pipeline
        if not stage_name or stage_name not in people_stages:
            stage_name = 'INFORMATION'  # Default
            
        stage = people_stages[stage_name]
        
        # Create pipeline contact
        pipeline_contact = PipelineContact(
            pipeline_id=people_pipeline.id,
            contact_id=person.id,
            current_stage_id=stage.id,
            entered_at=datetime.utcnow()
        )
        db.session.add(pipeline_contact)
        count += 1
        
        # If we've processed a batch, commit
        if count % 100 == 0:
            db.session.commit()
            print(f"Processed {count} people...")
    
    # Commit any remaining changes
    db.session.commit()
    print(f"Migrated {count} people to main pipeline.")

def migrate_churches(church_pipeline, church_stages):
    """Migrate all churches to the main church pipeline."""
    print("Migrating churches to main pipeline...")
    
    # Get all churches
    all_churches = Church.query.all()
    count = 0
    
    for church in all_churches:
        # Skip if already in the pipeline
        existing = PipelineContact.query.filter_by(
            pipeline_id=church_pipeline.id,
            contact_id=church.id
        ).first()
        
        if existing:
            continue
            
        # Get the appropriate stage based on church_pipeline value
        stage_name = church.church_pipeline
        if not stage_name or stage_name not in church_stages:
            stage_name = 'INFORMATION'  # Default
            
        stage = church_stages[stage_name]
        
        # Create pipeline contact
        pipeline_contact = PipelineContact(
            pipeline_id=church_pipeline.id,
            contact_id=church.id,
            current_stage_id=stage.id,
            entered_at=datetime.utcnow()
        )
        db.session.add(pipeline_contact)
        count += 1
        
        # If we've processed a batch, commit
        if count % 100 == 0:
            db.session.commit()
            print(f"Processed {count} churches...")
    
    # Commit any remaining changes
    db.session.commit()
    print(f"Migrated {count} churches to main pipeline.")

if __name__ == "__main__":
    # This allows the script to be run directly
    from app import create_app
    app = create_app()
    with app.app_context():
        migrate_contacts_to_main_pipelines() 