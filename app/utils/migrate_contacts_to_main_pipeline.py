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

def migrate_contacts_to_main_pipeline():
    """Migrate contacts to main pipelines if they aren't already in a pipeline."""
    try:
        # Get all main pipelines
        person_pipelines = Pipeline.query.filter_by(
            pipeline_type='person',
            is_main_pipeline=True
        ).all()
        
        church_pipelines = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True
        ).all()
        
        # Get all contacts not in any pipeline
        people_in_pipeline = db.session.query(PipelineContact.contact_id).join(
            Pipeline
        ).filter(
            Pipeline.pipeline_type == 'person'
        ).subquery()
        
        churches_in_pipeline = db.session.query(PipelineContact.contact_id).join(
            Pipeline
        ).filter(
            Pipeline.pipeline_type == 'church'
        ).subquery()
        
        people_to_migrate = Person.query.filter(
            Contact.id.notin_(people_in_pipeline)
        ).all()
        
        churches_to_migrate = Church.query.filter(
            Contact.id.notin_(churches_in_pipeline)
        ).all()
        
        # Migrate people
        for person in people_to_migrate:
            # Find the main pipeline for this person's office
            pipeline = next(
                (p for p in person_pipelines if p.office_id == person.office_id),
                None
            )
            
            if pipeline:
                # Get the first stage
                first_stage = PipelineStage.query.filter_by(
                    pipeline_id=pipeline.id
                ).order_by(PipelineStage.order).first()
                
                if first_stage:
                    pipeline_contact = PipelineContact(
                        pipeline_id=pipeline.id,
                        contact_id=person.id,
                        current_stage_id=first_stage.id
                    )
                    db.session.add(pipeline_contact)
        
        # Migrate churches
        for church in churches_to_migrate:
            # Find the main pipeline for this church's office
            pipeline = next(
                (p for p in church_pipelines if p.office_id == church.office_id),
                None
            )
            
            if pipeline:
                # Get the first stage
                first_stage = PipelineStage.query.filter_by(
                    pipeline_id=pipeline.id
                ).order_by(PipelineStage.order).first()
                
                if first_stage:
                    pipeline_contact = PipelineContact(
                        pipeline_id=pipeline.id,
                        contact_id=church.id,
                        current_stage_id=first_stage.id
                    )
                    db.session.add(pipeline_contact)
        
        db.session.commit()
        current_app.logger.info(f"Migrated {len(people_to_migrate)} people and {len(churches_to_migrate)} churches to main pipelines.")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error migrating contacts to main pipelines: {str(e)}")
        raise

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
        migrate_contacts_to_main_pipeline() 