from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.church import Church
from app.models.contact import Contact
from app.extensions import db
from datetime import datetime

app = create_app()

def fix_church_pipeline():
    """Check and fix the church pipeline to ensure all churches are correctly added."""
    with app.app_context():
        # Get the main church pipeline
        church_pipeline = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True,
            office_id=1  # Main Office
        ).first()
        
        if not church_pipeline:
            print("Main church pipeline not found")
            return
            
        print(f"Found main church pipeline: {church_pipeline.name} (ID: {church_pipeline.id})")
        
        # Get the stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).order_by(PipelineStage.order).all()
        if not stages:
            print("No stages found for church pipeline")
            return
            
        # Create a dictionary of stage names to stages
        stage_dict = {stage.name: stage for stage in stages}
        default_stage = stage_dict.get("INFORMATION") or stages[0]
        
        print(f"Default stage: {default_stage.name} (ID: {default_stage.id})")
        
        # Get all churches
        churches = Church.query.all()
        print(f"Found {len(churches)} churches in database")
        
        # Count churches already in pipeline
        existing_contacts = db.session.query(PipelineContact.contact_id).filter(
            PipelineContact.pipeline_id == church_pipeline.id
        ).all()
        existing_contact_ids = [contact[0] for contact in existing_contacts]
        print(f"Found {len(existing_contact_ids)} churches already in pipeline")
        print(f"Existing contact IDs: {existing_contact_ids}")
        
        # Get Contact IDs for churches
        church_contact_ids = []
        for church in churches:
            # Check if there's a corresponding Contact record
            contact = Contact.query.filter_by(id=church.id).first()
            if contact:
                church_contact_ids.append(contact.id)
        
        print(f"Found {len(church_contact_ids)} church contact IDs")
        print(f"Church contact IDs: {church_contact_ids}")
        
        # Find churches not in the pipeline
        missing_ids = set(church_contact_ids) - set(existing_contact_ids)
        print(f"Found {len(missing_ids)} churches missing from pipeline")
        
        # Add missing churches to pipeline
        count = 0
        for contact_id in missing_ids:
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
            
        # Commit changes
        db.session.commit()
        print(f"Added {count} churches to main pipeline")
        
if __name__ == "__main__":
    fix_church_pipeline() 