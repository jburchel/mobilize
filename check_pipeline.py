from app import create_app
from app.models.pipeline import Pipeline, PipelineContact
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Check total pipeline contacts
    contact_count = PipelineContact.query.count()
    print(f"Total pipeline contacts count: {contact_count}")
    
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