#!/usr/bin/env python3
"""
Test basic CRUD operations against PostgreSQL database

This script can be run locally (though connections may timeout)
or in a Cloud Run job where network connectivity to Supabase should work.
"""
import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Parse arguments
parser = argparse.ArgumentParser(description='Test CRUD operations against PostgreSQL')
parser.add_argument('--env', choices=['local', 'cloud'], default='local',
                    help='Environment where test is running (local or cloud)')
args = parser.parse_args()

# Set environment to production to use PostgreSQL
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

# Load environment variables
if args.env == 'local':
    load_dotenv('.env.production')
    print("Running in local environment (may encounter connection timeouts)")
else:
    print("Running in cloud environment (should have proper database connectivity)")

# Import app context and models after environment is set
try:
    from app import create_app
    from app.models.user import User
    from app.models.office import Office
    from app.models.task import Task
    from app.extensions import db
    
    app = create_app()
except Exception as e:
    print(f"Error during DB initialization: {e}")
    sys.exit(1)

def test_read_operations():
    """Test basic read operations on database"""
    print("\n=== TESTING READ OPERATIONS ===")
    
    with app.app_context():
        # Test reading users
        users = User.query.all()
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"  - {user.id}: {user.username} ({user.email})")
        
        # Test reading offices
        offices = Office.query.all()
        print(f"\nFound {len(offices)} offices:")
        for office in offices:
            print(f"  - {office.id}: {office.name}")
        
        # Test reading tasks
        tasks = Task.query.all()
        print(f"\nFound {len(tasks)} tasks:")
        for task in tasks:
            print(f"  - {task.id}: {task.title} (Status: {task.status})")
    
    return True

def test_create_operations():
    """Test creating new records in the database"""
    print("\n=== TESTING CREATE OPERATIONS ===")
    
    with app.app_context():
        try:
            # Create a test office
            office = Office(
                name=f"Test Office {int(time.time())}",
                address="123 Test St",
                city="Testville",
                state="TS",
                zip_code="12345",
                phone="555-123-4567",
                email="test@example.com",
                timezone="America/New_York",
                country="USA"
            )
            db.session.add(office)
            db.session.commit()
            print(f"Created new office with ID: {office.id}")
            
            # Create a test user
            user = User(
                username=f"testuser_{int(time.time())}",
                email=f"test_{int(time.time())}@example.com",
                first_name="Test",
                last_name="User",
                role="standard_user",
                office_id=office.id
            )
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()
            print(f"Created new user with ID: {user.id}")
            
            # Create a test task
            task = Task(
                title=f"Test Task {int(time.time())}",
                description="This is a test task",
                status="todo",
                priority="medium",
                due_date=datetime.now(),
                date_created=datetime.now(),
                assignee_id=user.id,
                owner_id=user.id
            )
            db.session.add(task)
            db.session.commit()
            print(f"Created new task with ID: {task.id}")
            
            return True, office.id, user.id, task.id
        
        except Exception as e:
            db.session.rollback()
            print(f"Error creating records: {e}")
            return False, None, None, None

def test_update_operations(office_id, user_id, task_id):
    """Test updating records in the database"""
    print("\n=== TESTING UPDATE OPERATIONS ===")
    
    with app.app_context():
        try:
            # Update office
            office = Office.query.get(office_id)
            if office:
                office.name = f"Updated Office {int(time.time())}"
                db.session.commit()
                print(f"Updated office {office_id} name to: {office.name}")
            
            # Update user
            user = User.query.get(user_id)
            if user:
                user.first_name = "Updated"
                user.last_name = "Name"
                db.session.commit()
                print(f"Updated user {user_id} name to: {user.first_name} {user.last_name}")
            
            # Update task
            task = Task.query.get(task_id)
            if task:
                task.status = "in_progress"
                task.priority = "high"
                db.session.commit()
                print(f"Updated task {task_id} status to: {task.status}, priority to: {task.priority}")
            
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"Error updating records: {e}")
            return False

def test_delete_operations(office_id, user_id, task_id):
    """Test deleting records from the database"""
    print("\n=== TESTING DELETE OPERATIONS ===")
    
    with app.app_context():
        try:
            # Delete task first (due to foreign key constraints)
            task = Task.query.get(task_id)
            if task:
                db.session.delete(task)
                db.session.commit()
                print(f"Deleted task with ID: {task_id}")
            
            # Delete user
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                print(f"Deleted user with ID: {user_id}")
            
            # Delete office
            office = Office.query.get(office_id)
            if office:
                db.session.delete(office)
                db.session.commit()
                print(f"Deleted office with ID: {office_id}")
            
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting records: {e}")
            return False

def main():
    print("Testing PostgreSQL CRUD operations...")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Test read operations first
    if not test_read_operations():
        print("❌ Read operations failed")
        return 1
    
    # Test create operations
    create_success, office_id, user_id, task_id = test_create_operations()
    if not create_success:
        print("❌ Create operations failed")
        return 1
    
    # Test update operations
    if not test_update_operations(office_id, user_id, task_id):
        print("❌ Update operations failed")
        return 1
    
    # Test delete operations
    if not test_delete_operations(office_id, user_id, task_id):
        print("❌ Delete operations failed")
        return 1
    
    print("\n✅ All CRUD operations completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 