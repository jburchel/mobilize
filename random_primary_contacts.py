#!/usr/bin/env python3
"""
Script to randomly select one person as the primary contact for each church.
"""
import random
import sys
from flask import Flask
from app import create_app
from app.models.church import Church
from app.models.person import Person
from app.extensions import db

def set_random_primary_contacts():
    """
    For each church, select one random person from its members
    and set that person as the church's primary contact.
    """
    # Get all churches
    churches = Church.query.all()
    print(f"Found {len(churches)} churches")
    
    changes_made = 0
    no_members = 0
    
    for church in churches:
        # Get people associated with this church
        church_members = Person.query.filter_by(church_id=church.id).all()
        
        if not church_members:
            print(f"Church {church.id}: {church.name} - No members found")
            no_members += 1
            continue
        
        # Select a random person from the members
        random_member = random.choice(church_members)
        
        # Set this person as the primary contact
        church.main_contact_id = random_member.id
        
        print(f"Church {church.id}: {church.name} - Set primary contact to {random_member.full_name} (ID: {random_member.id})")
        changes_made += 1
    
    # Commit the changes to the database
    db.session.commit()
    
    print(f"\nSummary:")
    print(f"- Total churches: {len(churches)}")
    print(f"- Churches with primary contacts set: {changes_made}")
    print(f"- Churches with no members: {no_members}")
    
    return changes_made

if __name__ == "__main__":
    # Create a minimal Flask application context
    app = create_app()
    
    with app.app_context():
        print("Starting random primary contact assignment...")
        changes = set_random_primary_contacts()
        print(f"Completed random primary contact assignment! {changes} primary contacts set.") 