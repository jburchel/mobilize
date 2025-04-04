"""
Utility to ensure all churches are properly added to the main church pipeline.
This can be imported and run when the Flask application starts.
"""
from app.extensions import db
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.church import Church
from app.models.contact import Contact
from datetime import datetime
from flask import current_app
from sqlalchemy import text
import time

def ensure_churches_in_pipeline():
    """Check and ensure all churches are in the main church pipeline."""
    try:
        # Get the main church pipeline
        church_pipeline = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True,
            office_id=1  # Main Office
        ).first()
        
        if not church_pipeline:
            current_app.logger.error("Main church pipeline not found")
            return
            
        current_app.logger.info(f"Found main church pipeline: {church_pipeline.name} (ID: {church_pipeline.id})")
        
        # Get the stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).order_by(PipelineStage.order).all()
        if not stages:
            current_app.logger.error("No stages found for church pipeline")
            return
            
        # Create a dictionary of stage names to stages
        stage_dict = {stage.name: stage for stage in stages}
        default_stage = stage_dict.get("INFORMATION") or stages[0]
        
        # Get all churches
        churches = Church.query.all()
        
        # Count churches already in pipeline
        existing_contacts = db.session.query(PipelineContact.contact_id).filter(
            PipelineContact.pipeline_id == church_pipeline.id
        ).all()
        existing_contact_ids = [contact[0] for contact in existing_contacts]
        
        # Get Contact IDs for churches
        church_contact_ids = []
        for church in churches:
            # Check if there's a corresponding Contact record
            contact = Contact.query.filter_by(id=church.id).first()
            if contact:
                church_contact_ids.append(contact.id)
        
        # Find churches not in the pipeline
        missing_ids = set(church_contact_ids) - set(existing_contact_ids)
        
        if missing_ids:
            current_app.logger.info(f"Found {len(missing_ids)} churches missing from pipeline. Adding them...")
            
            # Add missing churches to pipeline
            count = 0
            for contact_id in missing_ids:
                try:
                    # Check if this contact already exists in pipeline first
                    existing = db.session.execute(
                        text("SELECT id FROM pipeline_contacts WHERE pipeline_id = :pipeline_id AND contact_id = :contact_id"),
                        {"pipeline_id": church_pipeline.id, "contact_id": contact_id}
                    ).fetchone()
                    
                    if existing:
                        continue
                        
                    # Create pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=church_pipeline.id,
                        contact_id=contact_id,
                        current_stage_id=default_stage.id,
                        entered_at=datetime.now(),
                        last_updated=datetime.now()
                    )
                    
                    db.session.add(pipeline_contact)
                    count += 1
                    
                    # Commit immediately for each contact to avoid transaction issues
                    db.session.commit()
                    
                except Exception as e:
                    current_app.logger.error(f"Error adding contact ID {contact_id}: {str(e)}")
                    db.session.rollback()
            
            current_app.logger.info(f"Added {count} churches to main pipeline")
            
            # Verify the contacts were added
            updated_contacts = db.session.query(PipelineContact.contact_id).filter(
                PipelineContact.pipeline_id == church_pipeline.id
            ).all()
            updated_contact_ids = [contact[0] for contact in updated_contacts]
            current_app.logger.info(f"After fix: Found {len(updated_contact_ids)} churches in pipeline")
        else:
            current_app.logger.info(f"All churches ({len(church_contact_ids)}) are already in the pipeline")
    
    except Exception as e:
        current_app.logger.error(f"Error ensuring churches in pipeline: {str(e)}")
        db.session.rollback()

# This can be called from app initialization
def init_app(app):
    """Initialize the church pipeline utilities with the app."""
    with app.app_context():
        ensure_churches_in_pipeline() 