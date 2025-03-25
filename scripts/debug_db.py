#!/usr/bin/env python3
"""
Script to debug the database directly with SQL.
"""

import os
import sys
from pathlib import Path
import sqlalchemy as sa

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db

def debug_db():
    """Debug database with direct SQL queries."""
    print("Debugging database with SQL queries...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Check pipeline_contacts table
            try:
                print("\n--- Pipeline Contacts Table ---")
                result = db.session.execute(sa.text("SELECT * FROM pipeline_contacts;"))
                rows = result.fetchall()
                print(f"Found {len(rows)} pipeline_contacts records")
                
                for row in rows:
                    print(f"ID: {row[0]}, Contact ID: {row[1]}, Pipeline ID: {row[2]}, Stage ID: {row[3]}")
                
                # Get contact info for each pipeline contact
                print("\n--- Contact Details ---")
                for row in rows:
                    contact_result = db.session.execute(
                        sa.text("SELECT id, type, first_name, last_name FROM contacts WHERE id = :contact_id"),
                        {"contact_id": row[1]}
                    )
                    contact = contact_result.fetchone()
                    if contact:
                        print(f"Contact ID: {contact[0]}, Type: {contact[1]}, Name: {contact[2]} {contact[3]}")
                    else:
                        print(f"No contact found with ID {row[1]}")
                
                # Check PipelineContact model fetch
                print("\n--- ORM Query Comparison ---")
                from app.models.pipeline import PipelineContact
                orm_pcs = PipelineContact.query.all()
                print(f"ORM Query returns {len(orm_pcs)} pipeline contacts")
                
                for pc in orm_pcs:
                    print(f"ORM PC: ID: {pc.id}, Contact ID: {pc.contact_id}, Pipeline ID: {pc.pipeline_id}")
                
            except Exception as e:
                print(f"Error executing pipeline_contacts query: {str(e)}")
            
    except Exception as e:
        print(f"\n❌ Error debugging database: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    debug_db() 