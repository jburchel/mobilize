#!/usr/bin/env python3
"""
Database initialization script.
This script creates all database tables and sets up initial relationships.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models import Contact, Person, Church, User, Office, Task, Communication, EmailSignature, GoogleToken, Permission
from app.models.relationships import setup_relationships

def init_db():
    """Initialize the database by creating all tables and setting up relationships."""
    # Set the database path
    instance_path = os.path.join(project_root, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'mobilize_crm.db')
    os.environ['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("Dropped all existing tables.")
        
        # Create all tables
        db.create_all()
        print("Created all tables.")
        
        # Set up relationships
        setup_relationships()
        print("Set up model relationships.")
        
        print("\nDatabase initialized successfully!")

if __name__ == '__main__':
    init_db() 