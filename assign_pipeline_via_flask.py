#!/usr/bin/env python3
import random
from datetime import datetime
from app import create_app
from app.models import Pipeline, PipelineStage, PipelineContact, Person, Contact
from app.extensions import db
from sqlalchemy import text

app = create_app()

def assign_random_stages():
    with app.app_context():
        # Get the main people pipeline explicitly by ID
        pipeline = Pipeline.query.get(1)  # Main Office People Pipeline
        
        if not pipeline:
            print("Main people pipeline (ID: 1) not found. Exiting.")
            return

        print(f"Found pipeline: ID={pipeline.id}, Name={pipeline.name}, Type={pipeline.pipeline_type}")
        
        # Get all pipeline stages
        stages = PipelineStage.query.filter_by(pipeline_id=pipeline.id).all()
        
        if not stages:
            print("No pipeline stages found for the people pipeline. Exiting.")
            return
        
        print(f"Found {len(stages)} pipeline stages")
        for stage in stages:
            print(f"  - {stage.id}: {stage.name}")
        
        # Get all people
        people = Person.query.all()
        
        print(f"Found {len(people)} people")
        
        # Current timestamp for the updates
        current_time = datetime.now()
        
        # First clean up any existing pipeline_contacts entries
        print("Cleaning up existing pipeline contacts...")
        deleted_count = PipelineContact.query.filter_by(pipeline_id=pipeline.id).delete()
        print(f"Deleted {deleted_count} existing pipeline contact entries.")
        
        # Verify the actual contacts table has entries
        contacts_count = Contact.query.count()
        print(f"Verifying contacts table: {contacts_count} entries")
        
        # Create lists for bulk operations
        pipeline_contacts = []
        
        for person in people:
            # Select a random stage
            stage = random.choice(stages)
            
            # First check if this person has a corresponding Contact entry
            contact_id = None
            
            # In a real app, there should be a direct relationship, but let's check the contacts table
            # Test if this person is already in the contacts table
            contact = Contact.query.get(person.id)
            if contact:
                contact_id = contact.id
                print(f"Found existing contact entry for person {person.id}")
            else:
                print(f"WARNING: No contact entry found for person {person.id}. Creating one.")
                # Create a new contact entry for this person
                new_contact = Contact(id=person.id, first_name=person.first_name, last_name=person.last_name)
                db.session.add(new_contact)
                db.session.flush()  # Get the ID without committing
                contact_id = new_contact.id
            
            # Create pipeline contact
            pipeline_contact = PipelineContact(
                contact_id=contact_id,
                pipeline_id=pipeline.id,
                current_stage_id=stage.id,
                entered_at=current_time,
                last_updated=current_time
            )
            
            pipeline_contacts.append(pipeline_contact)
            
            # Update person's pipeline stage directly
            person.pipeline_stage = stage.name
            
            print(f"Prepared person_id: {person.id}, contact_id: {contact_id}, stage_id: {stage.id}, stage_name: {stage.name}")
        
        # Add all pipeline contacts
        print("Adding pipeline contacts to session...")
        db.session.add_all(pipeline_contacts)
        
        # Commit changes
        print("Committing changes...")
        db.session.commit()
        print("Changes committed.")
        
        # Print summary
        print(f"Successfully assigned random pipeline stages to {len(people)} people")
        
        # Show distribution of stages
        print("Distribution:")
        stage_counts = {}
        for stage in stages:
            count = PipelineContact.query.filter_by(
                pipeline_id=pipeline.id, 
                current_stage_id=stage.id
            ).count()
            print(f"  {stage.name}: {count} people")
            stage_counts[stage.name] = count
        
        # Verify the pipeline_contacts table has entries
        final_count = PipelineContact.query.filter_by(pipeline_id=pipeline.id).count()
        print(f"Final verification: pipeline_contacts has {final_count} entries for pipeline_id {pipeline.id}")
        
        # Directly query the database to double-check
        sql_count = db.session.execute(
            text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
            {"pipeline_id": pipeline.id}
        ).scalar() or 0
        
        print(f"SQL verification: pipeline_contacts has {sql_count} entries for pipeline_id {pipeline.id}")
        
        # Debug model's count_contacts method
        model_count = pipeline.count_contacts()
        print(f"Model count_contacts(): {model_count}")
        
        return final_count

if __name__ == "__main__":
    assign_random_stages() 