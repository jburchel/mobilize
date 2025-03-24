#!/usr/bin/env python
"""
Script to list all people in the database.
"""
from app import create_app, db
from app.models.person import Person
from app.models.contact import Contact

app = create_app()

def list_people():
    """List all people in the database with their details."""
    with app.app_context():
        people = Person.query.all()
        print(f"Found {len(people)} people:")
        
        for person in people:
            # Get the associated contact (every person should have one)
            contact = Contact.query.get(person.id)
            
            if contact:
                print(f"Person {person.id}: {person.first_name} {person.last_name}")
                print(f"  Contact info: {contact.email}, {contact.phone}, office_id={contact.office_id}")
                print(f"  Status: {person.status}")
                if person.associated_user:
                    print(f"  Associated user: {person.associated_user.username}")
                else:
                    print(f"  No associated user")
                print("-" * 40)
            else:
                print(f"Person {person.id}: {person.first_name} {person.last_name} (NO CONTACT RECORD)")

if __name__ == "__main__":
    list_people() 