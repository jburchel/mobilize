#!/usr/bin/env python3
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/mobilize_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define minimal models to avoid loading the entire app
class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    google_contact_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime)

class Person(Contact):
    __tablename__ = 'people'
    __mapper_args__ = {
        'polymorphic_identity': 'person'
    }
    id = db.Column(db.Integer, db.ForeignKey('contacts.id'), primary_key=True)

def get_count():
    """Get the counts of different types of contacts."""
    with app.app_context():
        total_contacts = Contact.query.count()
        google_contacts = Contact.query.filter(
            Contact.google_contact_id.isnot(None),
            Contact.type == 'contact'
        ).count()
        people = Person.query.count()
        google_people = Person.query.filter(
            Person.google_contact_id.isnot(None)
        ).count()
        
        print(f"Database Statistics:")
        print(f"-------------------")
        print(f"Total Contacts: {total_contacts}")
        print(f"Google Contacts (type='contact'): {google_contacts}")
        print(f"Total People: {people}")
        print(f"Google People: {google_people}")
        
def list_recently_imported():
    """List recently imported contacts for selection."""
    with app.app_context():
        # Get all people with Google IDs (sorted by most recently added)
        people = Person.query.filter(
            Person.google_contact_id.isnot(None)
        ).all()
        
        if not people:
            print("No imported people found in the database.")
            return []
            
        print(f"\nRecently Imported People:")
        print(f"------------------------")
        for i, person in enumerate(people, 1):
            print(f"{i}. {person.first_name} {person.last_name} (ID: {person.id}, Google ID: {person.google_contact_id})")
            
        return people
        
def list_all_contacts():
    """List all contacts for review."""
    with app.app_context():
        # Get all contacts
        contacts = Contact.query.filter(Contact.type == 'contact').all()
        
        if not contacts:
            print("No generic contacts found in the database.")
            return []
            
        print(f"\nGeneric Contacts (type='contact'):")
        print(f"----------------------------------")
        for i, contact in enumerate(contacts, 1):
            print(f"{i}. {contact.first_name} {contact.last_name} (ID: {contact.id}, Type: {contact.type})")
            
        return contacts

def delete_person(person_id):
    """Delete a person by ID."""
    with app.app_context():
        person = Person.query.get(person_id)
        if not person:
            print(f"Person with ID {person_id} not found.")
            return False
            
        name = f"{person.first_name} {person.last_name}"
        db.session.delete(person)
        db.session.commit()
        print(f"Deleted person: {name} (ID: {person_id})")
        return True
        
def delete_contact(contact_id):
    """Delete a contact by ID."""
    with app.app_context():
        contact = Contact.query.get(contact_id)
        if not contact:
            print(f"Contact with ID {contact_id} not found.")
            return False
            
        name = f"{contact.first_name} {contact.last_name}"
        db.session.delete(contact)
        db.session.commit()
        print(f"Deleted contact: {name} (ID: {contact_id})")
        return True

def main():
    """Main function to manage Google-imported contacts."""
    get_count()
    
    while True:
        print("\nOptions:")
        print("1. List and delete imported people")
        print("2. List and delete generic contacts")
        print("3. Check database stats")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            recent_people = list_recently_imported()
            if not recent_people:
                continue
                
            person_num = input("Enter the number of the person to delete (or 'all' to delete all): ")
            if person_num.lower() == 'all':
                confirm = input("Are you sure you want to delete ALL imported people? (y/n): ")
                if confirm.lower() == 'y':
                    for person in recent_people:
                        delete_person(person.id)
                    print("All imported people deleted.")
            else:
                try:
                    idx = int(person_num) - 1
                    if 0 <= idx < len(recent_people):
                        delete_person(recent_people[idx].id)
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a valid number or 'all'.")
        
        elif choice == '2':
            contacts = list_all_contacts()
            if not contacts:
                continue
                
            contact_num = input("Enter the number of the contact to delete (or 'all' to delete all): ")
            if contact_num.lower() == 'all':
                confirm = input("Are you sure you want to delete ALL generic contacts? (y/n): ")
                if confirm.lower() == 'y':
                    for contact in contacts:
                        delete_contact(contact.id)
                    print("All generic contacts deleted.")
            else:
                try:
                    idx = int(contact_num) - 1
                    if 0 <= idx < len(contacts):
                        delete_contact(contacts[idx].id)
                    else:
                        print("Invalid selection.")
                except ValueError:
                    print("Please enter a valid number or 'all'.")
        
        elif choice == '3':
            get_count()
            
        elif choice == '4':
            print("Exiting...")
            break
            
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main() 