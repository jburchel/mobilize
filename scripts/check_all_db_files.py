#!/usr/bin/env python3
"""
Script to check all database files in the project.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_all_db_files():
    """Check all database files in the project."""
    print("Checking all database files in the project...")
    
    # Find all .db files
    db_files = list(project_root.glob("**/*.db"))
    print(f"Found {len(db_files)} database files:")
    
    for db_file in db_files:
        relative_path = db_file.relative_to(project_root)
        print(f"\n=== Checking {relative_path} ===")
        
        try:
            # Connect to the database
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables: {[t[0] for t in tables]}")
            
            # Check for pipeline_contacts table
            if ('pipeline_contacts',) in tables:
                print("pipeline_contacts table exists")
                
                # Check count
                cursor.execute("SELECT COUNT(*) FROM pipeline_contacts;")
                count = cursor.fetchone()[0]
                print(f"pipeline_contacts count: {count}")
                
                if count > 0:
                    # Get a sample
                    cursor.execute("SELECT * FROM pipeline_contacts LIMIT 5;")
                    sample = cursor.fetchall()
                    print(f"Sample records: {sample}")
            else:
                print("pipeline_contacts table does not exist")
            
            # Close connection
            conn.close()
            
        except Exception as e:
            print(f"Error checking database {db_file}: {str(e)}")
    
    # Now check the Flask app's configured database
    from app import create_app
    
    app = create_app()
    
    with app.app_context():
        print("\n=== Checking Flask app's configured database ===")
        print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Get the database path from the URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri[10:]  # Remove sqlite:///
            
            # If it's a relative path, make it absolute
            if not os.path.isabs(db_path):
                db_path = os.path.join(project_root, db_path)
            
            print(f"Database path: {db_path}")
            
            # Check if the file exists
            if os.path.exists(db_path):
                print(f"Database file exists at {db_path}")
            else:
                print(f"Database file does NOT exist at {db_path}")
        else:
            print(f"Not a SQLite database URI: {db_uri}")

if __name__ == "__main__":
    check_all_db_files() 