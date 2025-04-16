#!/usr/bin/env python
"""
Script to create Person records for all existing users and link them together.
"""
from app import create_app
from app.models.user import User
from app.extensions import db
from app.utils.user_utils import create_person_for_user
import sys

app = create_app()

def migrate_users_to_people():
    """
    Create a Person record for each User that doesn't already have one,
    and link them together.
    """
    with app.app_context():
        # Get all users without a linked person record
        users_without_person = User.query.filter(User.person_id.is_(None)).all()
        
        print(f"Found {len(users_without_person)} users without Person records")

        if not users_without_person:
            print("No users need Person records. Exiting.")
            sys.exit(0)
        
        total_created = 0
        for user in users_without_person:
            try:
                # Skip users without required fields
                if not user.email or not user.office_id:
                    print(f"Skipping user {user.username}: missing required fields")
                    continue
                
                # Create person record using the utility function
                person = create_person_for_user(user)
                print(f"Created Person record (ID {person.id}) for user {user.username}")
                total_created += 1
                
            except Exception as e:
                print(f"Error creating Person record for {user.username}: {str(e)}")
                continue
            
        print(f"Migration completed. Created {total_created} Person records.")

if __name__ == "__main__":
    migrate_users_to_people() 