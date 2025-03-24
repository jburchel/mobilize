#!/usr/bin/env python
"""
Script to create Person records for all existing users and link them together.
"""
from app import create_app, db
from app.models.user import User
from app.models.person import Person
from app.models.contact import Contact
from app.models.office import Office
from datetime import datetime
import sys
from sqlalchemy import text

app = create_app()

def create_person_records_for_users():
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
        
        # Make sure we have a valid office ID
        default_office = Office.query.first()
        if not default_office:
            print("Error: No office found in the database. Please create an office first.")
            sys.exit(1)
        
        default_office_id = default_office.id
        print(f"Using default office ID: {default_office_id}")
        
        # For each user, create a person record
        for user in users_without_person:
            # Skip if email is missing - we can't create a valid contact without an email
            if not user.email:
                print(f"Skipping user {user.username} because email is missing")
                continue
                
            # First check if a contact with the same email exists
            existing_contact = Contact.query.filter(Contact.email == user.email).first()
            
            if existing_contact:
                # Check if there's already a person record for this contact
                existing_person = Person.query.filter(Person.id == existing_contact.id).first()
                if existing_person:
                    print(f"Found existing Person record for {user.username} with email {user.email}")
                    # Update user's person_id using direct SQL to avoid ORM conflicts
                    db.session.execute(
                        text("UPDATE users SET person_id = :person_id WHERE id = :user_id"),
                        {"person_id": existing_person.id, "user_id": user.id}
                    )
                    db.session.commit()
                    continue
            
            print(f"Creating new Person record for {user.username} ({user.email})")
            
            # Determine office ID
            office_id = user.office_id if user.office_id is not None else default_office_id
            
            # Use direct SQL to create contact record
            result = db.session.execute(
                text("""
                INSERT INTO contacts 
                (type, first_name, last_name, email, phone, office_id, created_at, updated_at)
                VALUES 
                (:type, :first_name, :last_name, :email, :phone, :office_id, :created_at, :updated_at)
                RETURNING id
                """),
                {
                    "type": "person",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "email": user.email,
                    "phone": user.phone or "",
                    "office_id": office_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            )
            contact_id = result.fetchone()[0]
            
            # Use direct SQL to create person record
            db.session.execute(
                text("""
                INSERT INTO people 
                (id, first_name, last_name, status, is_primary_contact)
                VALUES 
                (:id, :first_name, :last_name, :status, :is_primary_contact)
                """),
                {
                    "id": contact_id,
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "status": "active",
                    "is_primary_contact": False
                }
            )
            
            # Update user's person_id
            db.session.execute(
                text("UPDATE users SET person_id = :person_id WHERE id = :user_id"),
                {"person_id": contact_id, "user_id": user.id}
            )
            
            print(f"Created new Person record (ID {contact_id}) for {user.username}")
            db.session.commit()
            
        print("All users now have associated Person records")

if __name__ == "__main__":
    create_person_records_for_users() 