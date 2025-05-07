#!/usr/bin/env python3
"""
Script to generate sample communications and tasks data for Mobilize CRM.
This script focuses only on creating communications and tasks for testing.
"""

import sys
from pathlib import Path
import random
from datetime import datetime, timedelta
from faker import Faker

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Set up the Flask application context for database operations
from app import create_app, db
from app.models.user import User
from app.models.person import Person
from app.models.church import Church
from app.models.task import Task, TaskStatus, TaskPriority, TaskType
from app.models.communication import Communication
from app.models.office import Office

# Initialize faker
fake = Faker()

def generate_sample_data():
    """Generate sample communications and tasks data."""
    print("Starting sample data generation...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Get existing users, people, and churches
            users = User.query.all()
            if not users:
                print("Error: No users found! Please set up users first.")
                return
            print(f"✓ Found {len(users)} users to work with.")
            
            people = Person.query.all()
            print(f"✓ Found {len(people)} people to work with.")
            
            churches = Church.query.all()
            print(f"✓ Found {len(churches)} churches to work with.")
            
            offices = Office.query.all()
            print(f"✓ Found {len(offices)} offices to work with.")
            
            print("Step 1/2: Creating sample tasks...")
            # Create sample tasks
            create_sample_tasks(users, people, churches)
            
            print("Step 2/2: Creating sample communications...")
            # Create sample communications
            create_sample_communications(users, people, churches)
            
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

def create_sample_tasks(users, people, churches):
    """Create sample tasks for testing."""
    print("Creating sample tasks...")
    
    # Make sure we don't create too many duplicate tasks
    existing_tasks = Task.query.count()
    print(f"Current task count: {existing_tasks}")
    
    if existing_tasks > 50:
        print("Sufficient tasks already exist, skipping creation.")
        return
    
    # Number of tasks to create
    num_tasks = 30
    print(f"Starting to create {num_tasks} sample tasks...")
    
    task_categories = ["Follow-up", "Meeting", "Phone Call", "Email", "Research", "Administrative"]
    task_data = []
    
    for i in range(num_tasks):
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
        
        # Assign to a random user
        owner = random.choice(users)
        assigned_user = random.choice(users)
        
        # Generate due date (between now and 30 days in the future)
        due_date = datetime.now() + timedelta(days=random.randint(1, 30))
        
        # Randomly set status
        if random.random() < 0.7:
            status = TaskStatus.PENDING.value
        else:
            status = random.choice([status.value for status in TaskStatus])
        
        # Create completion date if task is completed
        completed_at = datetime.now() - timedelta(days=random.randint(0, 5)) if status == TaskStatus.COMPLETED.value else None
        
        task = Task(
            title=f"{random.choice(task_categories)} - {contact.get_name() if hasattr(contact, 'get_name') else 'Contact'}",
            description=fake.paragraph(),
            due_date=due_date,
            due_time=f"{random.randint(8, 17)}:{random.choice(['00', '15', '30', '45'])}",
            reminder_option=random.choice(["15_min", "30_min", "1_hour", "2_hours", "1_day", "3_days", "1_week", "none"]),
            priority=random.choice([priority.value for priority in TaskPriority]),
            status=status,
            type=random.choice([task_type.value for task_type in TaskType]),
            assigned_to=assigned_user.id,
            person_id=person_id,
            church_id=church_id,
            created_by=owner.id,
            owner_id=owner.id,
            office_id=owner.office_id,
            completed_at=completed_at,
            google_calendar_sync_enabled=random.choice([True, False])
        )
        
        db.session.add(task)
        task_data.append(task)
        
        if i % 10 == 0 and i > 0:
            print(f"Created {i} tasks so far...")
            db.session.flush()
    
    db.session.flush()
    print(f"Created {len(task_data)} sample tasks.")

def create_sample_communications(users, people, churches):
    """Create sample communications for testing."""
    print("Creating sample communications...")
    
    # Make sure we don't create too many duplicate communications
    existing_comms = Communication.query.count()
    print(f"Current communications count: {existing_comms}")
    
    if existing_comms > 50:
        print("Sufficient communications already exist, skipping creation.")
        return
    
    # Number of communications to create
    num_comms = 40
    print(f"Starting to create {num_comms} sample communications...")
    
    communication_types = ["email", "phone", "sms", "letter", "meeting"]
    communication_data = []
    
    for i in range(num_comms):
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
        
        communication = Communication(
            type=comm_type,
            message=fake.paragraph(),
            date_sent=date_sent,
            date=date_sent,
            person_id=person_id,
            church_id=church_id,
            user_id=owner.id,
            owner_id=owner.id,
            office_id=owner.office_id,
            direction=random.choice(["inbound", "outbound"]),
            gmail_message_id=gmail_message_id,
            gmail_thread_id=gmail_thread_id,
            email_status=email_status,
            subject=subject
        )
        
        db.session.add(communication)
        communication_data.append(communication)
        
        if i % 10 == 0 and i > 0:
            print(f"Created {i} communications so far...")
            db.session.flush()
    
    db.session.flush()
    print(f"Created {len(communication_data)} sample communications.")

if __name__ == "__main__":
    generate_sample_data()
