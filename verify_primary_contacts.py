#!/usr/bin/env python3
"""
Script to verify primary contacts for each church.
"""
from flask import Flask
from app import create_app
from app.models.church import Church
from app.models.person import Person

def verify_primary_contacts():
    """
    List all churches and their primary contacts.
    """
    # Get all churches
    churches = Church.query.all()
    print(f"Found {len(churches)} churches")
    
    churches_with_contact = 0
    churches_without_contact = 0
    
    print("\nChurches and Their Primary Contacts:")
    print("=" * 80)
    print(f"{'ID':<5} {'Church Name':<40} {'Primary Contact':<30} {'Contact ID':<10}")
    print("-" * 80)
    
    for church in churches:
        contact_name = "None"
        contact_id = "N/A"
        
        if church.main_contact_id:
            # Get the primary contact person
            contact = Person.query.get(church.main_contact_id)
            if contact:
                contact_name = contact.full_name
                contact_id = contact.id
                churches_with_contact += 1
            else:
                contact_name = "Invalid Reference"
                churches_without_contact += 1
        else:
            churches_without_contact += 1
        
        print(f"{church.id:<5} {church.name[:38]:<40} {contact_name:<30} {contact_id:<10}")
    
    print("-" * 80)
    print(f"\nSummary:")
    print(f"- Total churches: {len(churches)}")
    print(f"- Churches with primary contacts: {churches_with_contact}")
    print(f"- Churches without primary contacts: {churches_without_contact}")

if __name__ == "__main__":
    # Create a minimal Flask application context
    app = create_app()
    
    with app.app_context():
        print("Verifying primary contacts for churches...")
        verify_primary_contacts()
        print("Verification complete!") 