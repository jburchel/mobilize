#!/usr/bin/env python3
"""
Sample data generation script for Mobilize CRM.
This script creates a comprehensive set of sample data for testing all features of the CRM.
"""

import os
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta, date
import json
from faker import Faker

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set up the Flask application context for database operations
from app import create_app, db
from app.models.office import Office
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.models.task import Task
from app.models.communication import Communication
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact, PipelineStageHistory
from app.models.constants import (
    MARITAL_STATUS_CHOICES, PEOPLE_PIPELINE_CHOICES, PRIORITY_CHOICES,
    ASSIGNED_TO_CHOICES, SOURCE_CHOICES, CHURCH_ROLE_CHOICES, TASK_STATUS_CHOICES,
    TASK_PRIORITY_CHOICES, REMINDER_CHOICES, CHURCH_PIPELINE_CHOICES
)
from app.utils.setup_main_pipelines import setup_main_pipelines

# Initialize faker
fake = Faker()

def generate_sample_data():
    """Generate comprehensive sample data for the CRM."""
    print("Starting sample data generation...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            print("Step 1/8: Setting up main pipelines...")
            setup_main_pipelines()
            print("✓ Main pipelines set up.")
            
            # We'll assume we already have our testing users set up, just get them
            users = User.query.all()
            if not users:
                print("Error: No users found! Please set up users first.")
                return
            print(f"✓ Found {len(users)} users to work with.")
            
            print("Step 2/8: Checking/creating offices...")
            # Get existing offices
            offices = Office.query.all()
            if not offices:
                # Create sample offices if none exist
                create_sample_offices()
                offices = Office.query.all()
            print(f"✓ Working with {len(offices)} offices.")
            
            print("Step 3/8: Creating sample churches...")
            # Create sample churches
            create_sample_churches(offices, users)
            print("✓ Churches created.")
            
            print("Step 4/8: Creating sample people...")
            # Create sample people
            create_sample_people(offices, users)
            print("✓ People created.")
            
            print("Step 5/8: Linking people to churches...")
            # Link some people to churches
            link_people_to_churches()
            print("✓ People linked to churches.")
            
            print("Step 6/8: Creating pipeline data...")
            # Create pipeline data including stages and contacts
            create_sample_pipeline_data(offices)
            print("✓ Pipeline data created.")
            
            print("Step 7/8: Creating sample tasks...")
            # Create sample tasks
            create_sample_tasks(users)
            print("✓ Tasks created.")
            
            print("Step 8/8: Creating sample communications...")
            # Create sample communications
            create_sample_communications(users)
            print("✓ Communications created.")
            
            # Commit all changes
            print("Committing all changes to database...")
            db.session.commit()
            
            print("✅ Sample data generation complete!")
            
    except Exception as e:
        print(f"\n❌ Error during sample data generation: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
        return

def create_sample_offices():
    """Create sample offices for testing."""
    print("Creating sample offices...")
    
    office_data = [
        {
            "name": "Mobilize Global HQ",
            "address": "123 Mission Way",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75201",
            "phone": "214-555-1000",
            "email": "hq@mobilizecorp.org"
        },
        {
            "name": "West Coast Office",
            "address": "456 Golden Gate Ave",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94102",
            "phone": "415-555-2000",
            "email": "westcoast@mobilizecorp.org"
        },
        {
            "name": "Midwest Regional Center",
            "address": "789 Lake Shore Dr",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60611",
            "phone": "312-555-3000",
            "email": "midwest@mobilizecorp.org"
        }
    ]
    
    for data in office_data:
        office = Office(**data)
        db.session.add(office)
    
    db.session.commit()
    print(f"Created {len(office_data)} sample offices.")

def create_sample_churches(offices, users):
    """Create sample churches for testing."""
    import sys
    
    print("Creating sample churches...", flush=True)
    
    try:
        # Make sure we have enough churches for a good test dataset
        current_count = Church.query.count()
        print(f"Current church count: {current_count}", flush=True)
        if current_count > 20:
            print("Sufficient churches already exist, skipping creation.", flush=True)
            return
        
        # Define US states for proper state values
        states = [
            "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
            "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
            "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
            "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
            "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
        ]
        
        denominations = [
            "Baptist", "Lutheran", "Methodist", "Presbyterian", "Catholic",
            "Episcopal", "Non-denominational", "Pentecostal", "Alliance",
            "Evangelical Free", "Christian Reformed", "Assembly of God"
        ]
        
        created_churches = []  # Keep track of created churches
        
        print(f"Starting to create 30 sample churches...", flush=True)
        # Create 30 sample churches
        for i in range(30):
            try:
                print(f"\nProcessing church {i+1}/30...", flush=True)
                office = random.choice(offices)
                
                # Find users in this office
                office_users = [u for u in users if u.office_id == office.id]
                
                # If we found users in this office, pick one randomly
                if office_users:
                    owner = random.choice(office_users)
                else:
                    # If no users in this office, just pick any user
                    owner = random.choice(users)
                    print(f"Warning: No users found in office {office.name}, assigning to random user", flush=True)
                
                print(f"Selected office: {office.name}", flush=True)
                print(f"Selected owner: {owner.email}", flush=True)
                
                church_name = f"{fake.city()} {random.choice(['Community', 'Bible', 'Fellowship', 'Christian', 'Gospel'])} Church"
                print(f"Generated church name: {church_name}", flush=True)
                
                email = f"info@{church_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.org"
                website = f"https://www.{church_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.org"
                
                # Create church instance directly instead of using dictionary
                try:
                    print("Creating church instance...", flush=True)
                    church = Church()
                    
                    # Base Contact fields
                    print("Setting base contact fields...", flush=True)
                    church.type = "church"  # Required for polymorphic identity
                    church.name = fake.company()
                    church.location = fake.city()
                    church.denomination = random.choice(["Baptist", "Methodist", "Presbyterian", "Catholic", "Non-denominational", "Lutheran", "Episcopal", "Assemblies of God", "Pentecostal", "Other"])
                    church.weekly_attendance = random.randint(50, 2000)
                    church.website = fake.url()
                    church.phone = fake.phone_number()
                    church.email = fake.company_email()
                    church.address = fake.street_address()
                    church.city = fake.city()
                    church.state = fake.state_abbr()
                    church.zip_code = fake.zipcode()
                    church.country = "USA"
                    church.notes = fake.paragraph()
                    church.office_id = office.id
                    
                    # Church-specific fields
                    print("Setting church-specific fields...", flush=True)
                    church.website = website
                    church.owner_id = owner.id
                    church.church_pipeline = random.choice([choice[0] for choice in CHURCH_PIPELINE_CHOICES])
                    church.priority = random.choice([choice[0] for choice in PRIORITY_CHOICES])
                    church.source = random.choice([choice[0] for choice in SOURCE_CHOICES])
                    church.senior_pastor_name = fake.name()
                    church.year_founded = random.randint(1900, 2020)
                    
                    # Important: Do not set main_contact_id yet to avoid circular dependency
                    
                    print("Adding church to session...", flush=True)
                    db.session.add(church)
                    created_churches.append(church)
                    
                    if i % 5 == 0:  # Commit every 5 churches
                        print(f"\nCommitting batch of churches (up to {i+1})...", flush=True)
                        db.session.commit()
                        print("Batch commit successful", flush=True)
                    
                    print(f"✓ Created church {i+1}/30: {church_name}", flush=True)
                    sys.stdout.flush()
                    
                except Exception as church_error:
                    print(f"\nError creating individual church {i+1}: {str(church_error)}", flush=True)
                    import traceback
                    print("\nFull error traceback:", flush=True)
                    print(traceback.format_exc(), flush=True)
                    db.session.rollback()
                    continue
                
            except Exception as e:
                print(f"\nError in church creation loop {i+1}: {str(e)}", flush=True)
                import traceback
                print("\nFull error traceback:", flush=True)
                print(traceback.format_exc(), flush=True)
                continue
        
        # Final commit for any remaining churches
        try:
            print("\nPerforming final commit...", flush=True)
            db.session.commit()
            final_count = Church.query.count()
            print(f"✅ Church creation complete. Total churches in database: {final_count}", flush=True)
            
        except Exception as e:
            print(f"\nError in final commit: {str(e)}", flush=True)
            import traceback
            print("\nFull error traceback:", flush=True)
            print(traceback.format_exc(), flush=True)
            db.session.rollback()
            
    except Exception as e:
        print(f"\nError in create_sample_churches: {str(e)}", flush=True)
        import traceback
        print("\nFull error traceback:", flush=True)
        print(traceback.format_exc(), flush=True)
        db.session.rollback()
        raise

def create_sample_people(offices, users):
    """Create sample people for testing."""
    print("Creating sample people...")
    
    # Make sure we have enough people for a good test dataset
    if Person.query.count() > 30:
        print("Sufficient people already exist, skipping creation.")
        return
    
    people_data = []
    
    # Create 50 sample people
    for i in range(50):
        office = random.choice(offices)
        
        # Find users in this office
        office_users = [u for u in users if u.office_id == office.id]
        
        # If we found users in this office, pick one randomly
        if office_users:
            owner = random.choice(office_users)
        else:
            # If no users in this office, just pick any user
            owner = random.choice(users)
            print(f"Warning: No users found in office {office.name}, assigning to random user")
        
        marital_status = random.choice([choice[0] for choice in MARITAL_STATUS_CHOICES])
        first_name = fake.first_name()
        
        person = {
            "first_name": first_name,
            "last_name": fake.last_name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "address": fake.street_address(),
            "city": fake.city(),
            "state": random.choice([choice[0] for choice in PRIORITY_CHOICES]),
            "zip_code": fake.zipcode(),
            "country": "USA",
            "notes": fake.paragraph(),
            "office_id": office.id,
            "user_id": owner.id,
            "preferred_contact_method": random.choice([choice[0] for choice in PRIORITY_CHOICES]),
            "people_pipeline": random.choice([choice[0] for choice in PEOPLE_PIPELINE_CHOICES]),
            "priority": random.choice([choice[0] for choice in PRIORITY_CHOICES]),
            "source": random.choice([choice[0] for choice in SOURCE_CHOICES]),
            "marital_status": marital_status,
            "type": "person",
            "title": random.choice(["Mr.", "Mrs.", "Ms.", "Dr.", "Rev."]) if random.random() > 0.3 else None
        }
        
        # Add spouse information if married
        if marital_status == "married":
            # Generate opposite gender name for spouse
            if random.random() > 0.5:  # Randomly decide gender
                person["spouse_first_name"] = fake.first_name_female()
            else:
                person["spouse_first_name"] = fake.first_name_male()
            person["spouse_last_name"] = person["last_name"]
        
        people_data.append(person)
        
        if i % 10 == 0:  # Print progress every 10 people
            print(f"Created {i+1}/50 people...")
    
    # Add people to database
    print("\nAdding people to database...")
    for data in people_data:
        person = Person(**data)
        db.session.add(person)
    
    try:
        print("Committing people to database...")
        db.session.commit()
        print(f"✅ Created {len(people_data)} sample people.")
    except Exception as e:
        print(f"Error committing people: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
        db.session.rollback()
        raise

def link_people_to_churches():
    """Link people to churches and set primary contacts."""
    print("Linking people to churches...", flush=True)
    
    # Get all people and churches
    people = Person.query.all()
    churches = Church.query.all()
    
    print(f"Found {len(people)} people and {len(churches)} churches to link", flush=True)
    
    # First pass: Link people to churches and set roles
    try:
        for person in people:
            if random.random() < 0.7:  # 70% chance of being linked to a church
                church = random.choice(churches)
                person.church = church
                person.church_role = random.choice([role[0] for role in CHURCH_ROLE_CHOICES])
                print(f"Linked {person.get_name()} to {church.name} as {person.church_role}", flush=True)
        
        print("\nCommitting initial person-church links...", flush=True)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error linking people to churches: {str(e)}", flush=True)
        print("\nFull error traceback:", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        return
    
    print("\nSetting primary contacts for churches...", flush=True)
    
    # Second pass: Set primary contacts for churches
    try:
        for church in churches:
            if random.random() < 0.1:  # 10% chance of setting a primary contact
                # Get all members of this church
                members = [p for p in people if p.church_id == church.id]
                if members:
                    primary_contact = random.choice(members)
                    church.main_contact = primary_contact
                    print(f"Set {primary_contact.get_name()} as primary contact for {church.name}", flush=True)
        
        print("\nCommitting primary contact assignments...", flush=True)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error setting primary contacts: {str(e)}", flush=True)
        print("\nFull error traceback:", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        return
    
    print("✓ People linked to churches and primary contacts set.", flush=True)

def create_sample_pipeline_data(offices):
    """Create sample pipeline data."""
    print("Creating sample pipeline data...", flush=True)
    
    try:
        # Get all people and churches as Contact instances
        from app.models.base import Contact
        from app.models.person import Person
        from app.models.church import Church
        
        people = Person.query.all()
        churches = Church.query.all()
        
        pipeline_map = {}  # Track pipelines by office_id
        
        print(f"Found {len(people)} people and {len(churches)} churches to process", flush=True)
        
        # First, get all existing main pipelines and stages
        people_pipelines = Pipeline.query.filter_by(
            pipeline_type="people",
            is_main_pipeline=True
        ).all()
        
        church_pipelines = Pipeline.query.filter_by(
            pipeline_type="church",
            is_main_pipeline=True
        ).all()
        
        print(f"Found {len(people_pipelines)} people pipelines and {len(church_pipelines)} church pipelines", flush=True)
        
        # Create a map of office_id -> pipeline_id for both people and church pipelines
        for pipeline in people_pipelines:
            if pipeline.office_id not in pipeline_map:
                pipeline_map[pipeline.office_id] = {}
            pipeline_map[pipeline.office_id]['people'] = pipeline
        
        for pipeline in church_pipelines:
            if pipeline.office_id not in pipeline_map:
                pipeline_map[pipeline.office_id] = {}
            pipeline_map[pipeline.office_id]['church'] = pipeline
        
        # Process each office
        for office in offices:
            print(f"\nProcessing office: {office.name}", flush=True)
            
            # Skip if we don't have pipelines for this office
            if office.id not in pipeline_map or 'people' not in pipeline_map[office.id] or 'church' not in pipeline_map[office.id]:
                print(f"Warning: Missing main pipelines for office {office.name}", flush=True)
                continue
            
            people_pipeline = pipeline_map[office.id]['people']
            church_pipeline = pipeline_map[office.id]['church']
            
            print(f"Using people pipeline ID {people_pipeline.id} and church pipeline ID {church_pipeline.id}", flush=True)
            
            # Get first stage of each pipeline
            people_first_stage = PipelineStage.query.filter_by(
                pipeline_id=people_pipeline.id
            ).order_by(PipelineStage.order).first()
            
            church_first_stage = PipelineStage.query.filter_by(
                pipeline_id=church_pipeline.id
            ).order_by(PipelineStage.order).first()
            
            if not people_first_stage or not church_first_stage:
                print(f"Warning: Missing stages for pipelines in office {office.name}", flush=True)
                continue
            
            print(f"Using people first stage ID {people_first_stage.id} and church first stage ID {church_first_stage.id}", flush=True)
            
            # First delete any existing pipeline contacts for these pipelines
            existing_people = PipelineContact.query.filter_by(pipeline_id=people_pipeline.id).all()
            for pc in existing_people:
                db.session.delete(pc)
                
            existing_churches = PipelineContact.query.filter_by(pipeline_id=church_pipeline.id).all()
            for pc in existing_churches:
                db.session.delete(pc)
                
            # Commit deletes
            db.session.commit()
            
            # Add people to pipeline (only if they belong to this office and aren't already in pipeline)
            office_people = [p for p in people if p.office_id == office.id]
            print(f"Found {len(office_people)} people in office {office.name}", flush=True)
            
            people_to_add = []
            for person in office_people:
                if random.random() < 0.4:  # 40% chance to add to pipeline
                    people_to_add.append(person)
            
            print(f"Selected {len(people_to_add)} people to add to pipeline", flush=True)
            
            for person in people_to_add:
                # Get the Person as a Contact instance
                contact_id = person.id
                contact = Contact.query.get(contact_id)
                
                if contact:
                    print(f"Adding person {person.get_name()} (ID: {contact_id}, Type: {contact.type}) to people pipeline", flush=True)
                    
                    # Create a new pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=people_pipeline.id,
                        contact_id=contact_id,
                        current_stage_id=people_first_stage.id,
                        entered_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                        last_updated=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    
                    # Add to session and commit immediately to ensure it's saved
                    db.session.add(pipeline_contact)
                    db.session.flush()
                else:
                    print(f"Warning: Could not find contact with ID {contact_id}", flush=True)
            
            # Commit people pipeline contacts
            db.session.commit()
            
            # Add churches to pipeline (only if they belong to this office and aren't already in pipeline)
            office_churches = [c for c in churches if c.office_id == office.id]
            print(f"Found {len(office_churches)} churches in office {office.name}", flush=True)
            
            churches_to_add = []
            for church in office_churches:
                if random.random() < 0.4:  # 40% chance to add to pipeline
                    churches_to_add.append(church)
            
            print(f"Selected {len(churches_to_add)} churches to add to pipeline", flush=True)
            
            for church in churches_to_add:
                # Get the Church as a Contact instance
                contact_id = church.id
                contact = Contact.query.get(contact_id)
                
                if contact:
                    print(f"Adding church {church.get_name()} (ID: {contact_id}, Type: {contact.type}) to church pipeline", flush=True)
                    
                    # Create a new pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=church_pipeline.id,
                        contact_id=contact_id,
                        current_stage_id=church_first_stage.id,
                        entered_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                        last_updated=datetime.now() - timedelta(days=random.randint(0, 30))
                    )
                    
                    # Add to session and commit immediately to ensure it's saved
                    db.session.add(pipeline_contact)
                    db.session.flush()
                else:
                    print(f"Warning: Could not find contact with ID {contact_id}", flush=True)
            
            # Commit church pipeline contacts
            db.session.commit()
        
        # Final commit to ensure all changes are saved
        db.session.commit()
        
        # Verify counts
        total_people_contacts = 0
        total_church_contacts = 0
        for office in offices:
            if office.id in pipeline_map and 'people' in pipeline_map[office.id]:
                people_count = PipelineContact.query.filter_by(pipeline_id=pipeline_map[office.id]['people'].id).count()
                total_people_contacts += people_count
                print(f"Office {office.name} has {people_count} people in pipeline", flush=True)
                
            if office.id in pipeline_map and 'church' in pipeline_map[office.id]:
                church_count = PipelineContact.query.filter_by(pipeline_id=pipeline_map[office.id]['church'].id).count()
                total_church_contacts += church_count
                print(f"Office {office.name} has {church_count} churches in pipeline", flush=True)
                
        print(f"Total: {total_people_contacts} people and {total_church_contacts} churches in pipelines", flush=True)
        print("✓ Pipeline data created.", flush=True)
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Error during pipeline data generation: {str(e)}", flush=True)
        print("\nFull error traceback:", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)

def create_sample_tasks(users):
    """Create sample tasks for testing."""
    print("Creating sample tasks...")
    
    # Make sure we don't create too many duplicate tasks
    if Task.query.count() > 30:
        print("Sufficient tasks already exist, skipping creation.")
        return
    
    task_categories = ["Follow-up", "Meeting", "Application", "Interview", "Documentation", "Training", "Fundraising", "Communication"]
    
    people = Person.query.all()
    churches = Church.query.all()
    
    task_data = []
    
    # Create 40 sample tasks
    for i in range(40):
        # Randomly choose between assigning to person or church
        if random.random() > 0.5 and people:
            contact = random.choice(people)
            task_type = "person"
            person_id = contact.id
            church_id = None
        elif churches:
            contact = random.choice(churches)
            task_type = "church"
            person_id = None
            church_id = contact.id
        else:
            continue
        
        owner = random.choice(users)
        assigned_user = random.choice(users)
        
        # Generate random due date (between yesterday and 30 days in future)
        due_date = date.today() + timedelta(days=random.randint(-1, 30))
        
        # Determine status based on due date
        if due_date < date.today():
            status = random.choice(["completed", "cancelled"]) if random.random() > 0.3 else "pending"
        else:
            status = random.choice([choice[0] for choice in TASK_STATUS_CHOICES])
        
        # Create completion date if task is completed
        completed_date = datetime.now() - timedelta(days=random.randint(0, 5)) if status == "completed" else None
        
        task = {
            "title": f"{random.choice(task_categories)} - {contact.get_name()}",
            "description": fake.paragraph(),
            "due_date": due_date,
            "due_time": f"{random.randint(8, 17)}:{random.choice(['00', '15', '30', '45'])}",
            "reminder_option": random.choice([choice[0] for choice in REMINDER_CHOICES]),
            "priority": random.choice([choice[0] for choice in TASK_PRIORITY_CHOICES]),
            "status": status,
            "category": random.choice(task_categories),
            "assigned_to": str(assigned_user.id),
            "person_id": person_id,
            "church_id": church_id,
            "created_by": owner.id,
            "owner_id": owner.id,
            "office_id": owner.office_id,
            "completed_date": completed_date,
            "completion_notes": fake.paragraph() if completed_date else None
        }
        
        task_data.append(task)
    
    # Add tasks to database
    for data in task_data:
        task = Task(**data)
        db.session.add(task)
    
    db.session.commit()
    print(f"Created {len(task_data)} sample tasks.")

def create_sample_communications(users):
    """Create sample communications for testing."""
    print("Creating sample communications...")
    
    # Make sure we don't create too many duplicate communications
    if Communication.query.count() > 50:
        print("Sufficient communications already exist, skipping creation.")
        return
    
    communication_types = ["email", "phone", "sms", "letter", "meeting"]
    
    people = Person.query.all()
    churches = Church.query.all()
    
    communication_data = []
    
    # Create 60 sample communications
    for i in range(60):
        # Randomly choose between person or church
        if random.random() > 0.3 and people:
            contact = random.choice(people)
            person_id = contact.id
            church_id = None
        elif churches:
            contact = random.choice(churches)
            person_id = None
            church_id = contact.id
        else:
            continue
        
        owner = random.choice(users)
        comm_type = random.choice(communication_types)
        
        # Generate date (between 180 days ago and now)
        date_sent = datetime.now() - timedelta(days=random.randint(0, 180))
        
        # Email specific fields
        subject = None
        gmail_message_id = None
        gmail_thread_id = None
        email_status = None
        
        if comm_type == "email":
            subject = fake.sentence()
            if random.random() > 0.5:
                gmail_message_id = f"msg-{fake.uuid4()}"
                gmail_thread_id = f"thread-{fake.uuid4()}"
                email_status = random.choice(["sent", "draft", "failed"])
        
        communication = {
            "type": comm_type,
            "message": fake.paragraph(),
            "date_sent": date_sent,
            "date": date_sent,
            "person_id": person_id,
            "church_id": church_id,
            "user_id": owner.id,
            "owner_id": owner.id,
            "office_id": owner.office_id,
            "direction": random.choice(["inbound", "outbound"]),
            "gmail_message_id": gmail_message_id,
            "gmail_thread_id": gmail_thread_id,
            "email_status": email_status,
            "subject": subject
        }
        
        communication_data.append(communication)
    
    # Add communications to database
    for data in communication_data:
        communication = Communication(**data)
        db.session.add(communication)
    
    db.session.commit()
    print(f"Created {len(communication_data)} sample communications.")

if __name__ == "__main__":
    generate_sample_data() 