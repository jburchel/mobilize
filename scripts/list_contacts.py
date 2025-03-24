#!/usr/bin/env python
"""
Script to list all contacts in the database.
"""
from app import create_app, db
from app.models.contact import Contact
from app.models.person import Person

app = create_app()

def list_contacts():
    """List all contacts in the database with their details."""
    with app.app_context():
        contacts = Contact.query.all()
        print(f"Found {len(contacts)} contacts:")
        
        for contact in contacts:
            print(f"Contact {contact.id}: {contact.first_name} {contact.last_name}")
            print(f"  Email: {contact.email}, Phone: {contact.phone}")
            print(f"  Type: {contact.type}, Office ID: {contact.office_id}")
            
            # Check if there's a person record for this contact
            person = Person.query.filter(Person.id == contact.id).first()
            if person:
                print(f"  Has associated person record: Yes")
                if person.associated_user:
                    print(f"  Associated with user: {person.associated_user.username}")
            else:
                print(f"  Has associated person record: No")
            
            print("-" * 40)

if __name__ == "__main__":
    list_contacts() 