from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from datetime import datetime

app = create_app()

def populate_people_pipeline():
    """Add all people to the main people pipeline."""
    with app.app_context():
        # Get the main people pipeline
        people_pipeline = Pipeline.query.filter_by(
            pipeline_type='person',
            is_main_pipeline=True,
            office_id=1  # Main Office
        ).first()
        
        if not people_pipeline:
            print("Main people pipeline not found")
            # List all people pipelines to debug
            people_pipelines = Pipeline.query.filter_by(pipeline_type='person').all()
            print(f"Found {len(people_pipelines)} people pipelines:")
            for p in people_pipelines:
                print(f"  Pipeline {p.id}: {p.name} - Office: {p.office_id} - Main: {p.is_main_pipeline}")
            return
            
        print(f"Found main people pipeline: {people_pipeline.name} (ID: {people_pipeline.id})")
        
        # Get the stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=people_pipeline.id).order_by(PipelineStage.order).all()
        if not stages:
            print("No stages found for people pipeline")
            return
            
        # Create a dictionary of stage names to stages
        stage_dict = {stage.name: stage for stage in stages}
        default_stage = stage_dict["INFORMATION"] if "INFORMATION" in stage_dict else stages[0]
        
        # Get all people
        people = Person.query.all()
        print(f"Found {len(people)} people")
        
        # Count people already in pipeline
        existing_contacts = db.session.query(PipelineContact.contact_id).filter(
            PipelineContact.pipeline_id == people_pipeline.id
        ).all()
        existing_contact_ids = [contact[0] for contact in existing_contacts]
        print(f"Found {len(existing_contact_ids)} people already in pipeline")
        
        # Add people to pipeline
        count = 0
        for person in people:
            if person.id in existing_contact_ids:
                continue
                
            # Determine stage based on people_pipeline field
            stage = default_stage
            if hasattr(person, 'people_pipeline') and person.people_pipeline in stage_dict:
                stage = stage_dict[person.people_pipeline]
                
            # Create pipeline contact
            pipeline_contact = PipelineContact(
                pipeline_id=people_pipeline.id,
                contact_id=person.id,
                current_stage_id=stage.id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            db.session.add(pipeline_contact)
            count += 1
            
        # Commit changes
        db.session.commit()
        print(f"Added {count} people to main pipeline")
        
def populate_churches_pipeline():
    """Add all churches to the main churches pipeline."""
    with app.app_context():
        # Get the main churches pipeline
        churches_pipeline = Pipeline.query.filter_by(
            pipeline_type='church',
            is_main_pipeline=True,
            office_id=1  # Main Office
        ).first()
        
        if not churches_pipeline:
            print("Main churches pipeline not found")
            # List all church pipelines to debug
            church_pipelines = Pipeline.query.filter_by(pipeline_type='church').all()
            print(f"Found {len(church_pipelines)} church pipelines:")
            for p in church_pipelines:
                print(f"  Pipeline {p.id}: {p.name} - Office: {p.office_id} - Main: {p.is_main_pipeline}")
            return
            
        print(f"Found main churches pipeline: {churches_pipeline.name} (ID: {churches_pipeline.id})")
        
        # Get the stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=churches_pipeline.id).order_by(PipelineStage.order).all()
        if not stages:
            print("No stages found for churches pipeline")
            return
            
        # Create a dictionary of stage names to stages
        stage_dict = {stage.name: stage for stage in stages}
        default_stage = stage_dict["INFORMATION"] if "INFORMATION" in stage_dict else stages[0]
        
        # Get all churches
        churches = Church.query.all()
        print(f"Found {len(churches)} churches")
        
        # Count churches already in pipeline
        existing_contacts = db.session.query(PipelineContact.contact_id).filter(
            PipelineContact.pipeline_id == churches_pipeline.id
        ).all()
        existing_contact_ids = [contact[0] for contact in existing_contacts]
        print(f"Found {len(existing_contact_ids)} churches already in pipeline")
        
        # Add churches to pipeline
        count = 0
        for church in churches:
            if church.id in existing_contact_ids:
                continue
                
            # Determine stage based on church_pipeline field
            stage = default_stage
            if hasattr(church, 'church_pipeline') and church.church_pipeline in stage_dict:
                stage = stage_dict[church.church_pipeline]
                
            # Create pipeline contact
            pipeline_contact = PipelineContact(
                pipeline_id=churches_pipeline.id,
                contact_id=church.id,
                current_stage_id=stage.id,
                entered_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            db.session.add(pipeline_contact)
            count += 1
            
        # Commit changes
        db.session.commit()
        print(f"Added {count} churches to main pipeline")
        
if __name__ == "__main__":
    populate_people_pipeline()
    populate_churches_pipeline() 