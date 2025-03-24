#!/usr/bin/env python
"""
Script to list all offices in the database.
"""
from app import create_app, db
from app.models.office import Office

app = create_app()

def list_offices():
    """List all offices in the database with their details."""
    with app.app_context():
        offices = Office.query.all()
        print(f"Found {len(offices)} offices:")
        
        for office in offices:
            print(f"Office {office.id}: {office.name}")
            print(f"  Contact: {office.email}, {office.phone}")
            print(f"  Location: {office.city}, {office.state}, {office.country}")
            print(f"  Active: {office.is_active}")
            print("-" * 40)

if __name__ == "__main__":
    list_offices() 