from app import create_app, db
from app.models.pipeline import Pipeline, PipelineContact
from app.models.church import Church
from app.models.contact import Contact
from sqlalchemy import text
import sys

def check_church_pipeline():
    app = create_app()
    with app.app_context():
        # Get main church pipeline (ID 2)
        church_pipeline = Pipeline.query.get(2)
        
        if not church_pipeline:
            print("Church pipeline not found!")
            return
            
        print(f"Main Church Pipeline: {church_pipeline.name}")
        print(f"Pipeline type: {church_pipeline.pipeline_type}")
        
        # Count contacts in pipeline using the method
        contact_count = church_pipeline.count_contacts()
        print(f"Church contacts in pipeline (using count_contacts method): {contact_count}")
        
        # Direct SQL count
        raw_count = db.session.execute(
            text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": church_pipeline.id}
        ).scalar() or 0
        print(f"Raw SQL count of pipeline contacts: {raw_count}")
        
        # Get all pipeline_contacts directly
        direct_query = db.session.execute(
            text("SELECT id, contact_id, current_stage_id FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": church_pipeline.id}
        ).fetchall()
        print(f"Direct query found {len(direct_query)} pipeline contacts")
        
        # Print first 5 contacts from direct query
        print("First 5 pipeline contacts from direct query:")
        for i, row in enumerate(direct_query[:5]):
            print(f"  {i+1}. ID: {row[0]}, Contact ID: {row[1]}, Stage ID: {row[2]}")
        
        # Get total churches in database for comparison
        total_churches = Church.query.count()
        print(f"Total churches in database: {total_churches}")
        
        # Get all pipeline contacts for this pipeline using ORM
        pipeline_contacts = PipelineContact.query.filter_by(pipeline_id=church_pipeline.id).all()
        print(f"Pipeline contacts found via ORM: {len(pipeline_contacts)}")
        
        # Get the actual church contacts
        church_contacts = []
        for pc in pipeline_contacts:
            contact = Contact.query.get(pc.contact_id)
            if contact and contact.contact_type == 'church':
                church_contacts.append(contact)
                
        print(f"Church contacts found via ORM: {len(church_contacts)}")
        
        # Check for contact_ids that might be duplicated
        contact_ids = [pc.contact_id for pc in pipeline_contacts]
        if len(contact_ids) != len(set(contact_ids)):
            print("WARNING: Duplicate contact IDs found in pipeline!")
            from collections import Counter
            dupes = [item for item, count in Counter(contact_ids).items() if count > 1]
            print(f"Duplicate contact IDs: {dupes}")
        
        # Display first 5 churches in pipeline
        print("\nSample churches in pipeline:")
        for i, contact in enumerate(church_contacts[:5]):
            print(f"  {i+1}. {contact.get_name()}")
        
        # Adding a direct database connection check
        # This is to see if there might be multiple database connections causing issues
        try:
            engine = db.engine
            connection = engine.connect()
            result = connection.execute(text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = 2"))
            count = result.scalar()
            print(f"Direct engine connection count: {count}")
            connection.close()
        except Exception as e:
            print(f"Error with direct connection: {str(e)}")

if __name__ == "__main__":
    check_church_pipeline() 