#!/usr/bin/env python3
"""
Script to debug the pipeline contacts table directly using raw SQL.
"""

import os
import sys
import random
from pathlib import Path
from sqlalchemy import text
import sqlalchemy as sa
from datetime import datetime

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.person import Person
from app.models.church import Church

def debug_pipeline_contacts():
    """Debug pipeline contacts database issues."""
    print("Debugging pipeline contacts...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Get all tables in the database
            table_result = db.session.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in table_result]
            print(f"Database tables: {tables}")
            
            # Check if pipeline_contacts table exists
            if 'pipeline_contacts' in tables:
                # Count existing entries
                count_result = db.session.execute(sa.text("SELECT COUNT(*) FROM pipeline_contacts;"))
                count = count_result.scalar()
                print(f"Raw SQL count of pipeline_contacts: {count}")
                
                # View existing entries
                contacts_result = db.session.execute(sa.text("SELECT * FROM pipeline_contacts;"))
                contacts = contacts_result.fetchall()
                
                print(f"\nFound {len(contacts)} pipeline contacts:")
                for contact in contacts:
                    print(contact)
                
                # Get schema info
                schema_result = db.session.execute(sa.text("PRAGMA table_info(pipeline_contacts);"))
                schema = schema_result.fetchall()
                
                print("\nPipeline Contacts Schema:")
                for column in schema:
                    print(f"Column: {column}")
                
                # Count total contacts, people, and churches
                total_contacts = db.session.execute(sa.text("SELECT COUNT(*) FROM contacts;")).scalar()
                total_people = db.session.execute(sa.text("SELECT COUNT(*) FROM people;")).scalar()
                total_churches = db.session.execute(sa.text("SELECT COUNT(*) FROM churches;")).scalar()
                
                print(f"\nTotal contacts in database: {total_contacts}")
                print(f"Total people in database: {total_people}")
                print(f"Total churches in database: {total_churches}")
                
                # Try to add a test pipeline contact
                print("\nTrying to add a test pipeline contact:")
                
                # Get a random person contact
                person = Person.query.first()
                
                # Get a pipeline
                pipeline = Pipeline.query.first()
                
                # Get a stage from that pipeline
                stage = PipelineStage.query.filter_by(pipeline_id=pipeline.id).first()
                
                if person and pipeline and stage:
                    # Try using the ORM
                    try:
                        # Create a new pipeline contact
                        contact = PipelineContact(
                            contact_id=person.id,
                            pipeline_id=pipeline.id,
                            stage_id=stage.id,
                            notes="Test contact added for debugging",
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        db.session.add(contact)
                        db.session.commit()
                        
                        print(f"Test pipeline contact added with contact_id={person.id}, pipeline_id={pipeline.id}, stage_id={stage.id}")
                        
                        # Verify the contact was added
                        verify_result = db.session.execute(sa.text("SELECT COUNT(*) FROM pipeline_contacts;"))
                        verify_count = verify_result.scalar()
                        print(f"Updated pipeline_contacts count: {verify_count}")
                        
                    except Exception as e:
                        print(f"Error adding contact through ORM: {str(e)}")
                        db.session.rollback()
                        
                        # Try using raw SQL
                        try:
                            sql = sa.text("""
                                INSERT INTO pipeline_contacts (contact_id, pipeline_id, stage_id, notes, created_at, updated_at)
                                VALUES (:contact_id, :pipeline_id, :stage_id, :notes, :created_at, :updated_at)
                            """)
                            
                            db.session.execute(sql, {
                                'contact_id': person.id,
                                'pipeline_id': pipeline.id,
                                'stage_id': stage.id,
                                'notes': "Test contact added for debugging via SQL",
                                'created_at': datetime.now(),
                                'updated_at': datetime.now()
                            })
                            
                            db.session.commit()
                            
                            print(f"Test pipeline contact added via SQL with contact_id={person.id}, pipeline_id={pipeline.id}, stage_id={stage.id}")
                            
                            # Verify the contact was added
                            verify_result = db.session.execute(sa.text("SELECT COUNT(*) FROM pipeline_contacts;"))
                            verify_count = verify_result.scalar()
                            print(f"Updated pipeline_contacts count: {verify_count}")
                            
                        except Exception as sql_e:
                            print(f"Error adding contact through SQL: {str(sql_e)}")
                            db.session.rollback()
                else:
                    print("Could not find required Person, Pipeline, or Stage to create test contact")
            else:
                print("Error: pipeline_contacts table does not exist in the database!")
    except Exception as e:
        print(f"Error debugging pipeline contacts: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pipeline_contacts() 