from app import create_app
from app.models.pipeline import Pipeline, PipelineContact, PipelineStage
from app.models.person import Person
from app.models.church import Church
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check pipelines
    pipelines = Pipeline.query.all()
    print(f"Found {len(pipelines)} pipelines:")
    for p in pipelines:
        print(f"  Pipeline {p.id}: {p.name} - Type: {p.pipeline_type} - Office: {p.office_id} - Main: {p.is_main_pipeline}")
        
        # Check stages for this pipeline
        stages = PipelineStage.query.filter_by(pipeline_id=p.id).all()
        print(f"  Pipeline {p.id} has {len(stages)} stages:")
        for s in stages:
            print(f"    Stage {s.id}: {s.name} - Order: {s.order}")
            
        # Check contacts for this pipeline
        contacts = PipelineContact.query.filter_by(pipeline_id=p.id).all()
        print(f"  Pipeline {p.id} has {len(contacts)} contacts")
    
    # Check total contacts
    print(f"\nTotal Pipeline Contacts: {PipelineContact.query.count()}")
    
    # Check people and churches
    print(f"Total People: {Person.query.count()}")
    print(f"Total Churches: {Church.query.count()}")
    
    # Check the first few people to see if they have pipeline_people field set
    people = Person.query.limit(5).all()
    print("\nSample People:")
    for p in people:
        print(f"  Person {p.id}: {p.first_name} {p.last_name} - Pipeline: {getattr(p, 'people_pipeline', 'N/A')}")
        
    # Check the first few churches
    churches = Church.query.limit(5).all()
    print("\nSample Churches:")
    for c in churches:
        print(f"  Church {c.id}: {c.name} - Pipeline: {getattr(c, 'church_pipeline', 'N/A')}")

    # Check total pipeline contacts
    contact_count = PipelineContact.query.count()
    print(f"\nTotal pipeline contacts count: {contact_count}")
    
    # Check people pipeline contact count using the model method
    people_pipeline = Pipeline.query.filter_by(pipeline_type='person').first()
    if people_pipeline:
        print(f"People pipeline ID: {people_pipeline.id}")
        print(f"People pipeline contact count (model method): {people_pipeline.count_contacts()}")
    
    # Direct SQL query for verification
    result = db.session.execute(
        text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
        {"pipeline_id": 1}
    )
    print(f"People pipeline contact count (direct SQL): {result.scalar() or 0}")
    
    # List some actual entries
    contacts = PipelineContact.query.filter_by(pipeline_id=1).limit(5).all()
    print(f"\nSample pipeline contacts (first 5):")
    for contact in contacts:
        print(f"  - ID: {contact.id}, Pipeline ID: {contact.pipeline_id}, Contact ID: {contact.contact_id}, Stage ID: {contact.stage_id}") 