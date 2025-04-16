from datetime import datetime
from app.extensions import db
from app.models.user import User
from app.models.person import Person
from app.models.contact import Contact
from flask import current_app

def create_person_for_user(user):
    """
    Create a Person record for a User if they don't already have one.
    
    Args:
        user: A User object
        
    Returns:
        Person: The created or existing Person record
        
    Raises:
        ValueError: If the user doesn't have an email address or office_id
    """
    if user.person_id:
        # User already has a linked person
        return user.person
    
    if not user.email:
        raise ValueError("Cannot create a Person for a User without an email address")
    
    if not user.office_id:
        raise ValueError("Cannot create a Person for a User without an office_id")
    
    # Check if a Contact with the same email already exists
    existing_contact = Contact.query.filter_by(email=user.email).first()
    
    if existing_contact:
        # If there's a Person record for this Contact, use it
        existing_person = Person.query.filter_by(id=existing_contact.id).first()
        if existing_person:
            current_app.logger.info(f"Found existing Person record for {user.username} with email {user.email}")
            
            # Link the User to the Person
            user.person_id = existing_person.id
            db.session.commit()
            
            return existing_person
    
    # Create a new Person record
    current_app.logger.info(f"Creating new Person record for user {user.username} ({user.email})")
    
    person = Person(
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        email=user.email,
        phone=user.phone or "",
        type='person',
        office_id=user.office_id,
        user_id=user.id,
        status='active',
        is_primary_contact=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.session.add(person)
    db.session.flush()  # Get the ID without committing
    
    # Link the User to the Person
    user.person_id = person.id
    db.session.commit()
    
    current_app.logger.info(f"Created new Person record (ID {person.id}) for {user.username}")
    
    return person 