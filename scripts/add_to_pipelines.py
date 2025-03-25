#!/usr/bin/env python
"""Script to add contacts to pipelines using raw SQL."""
import sys
import os
from pathlib import Path
import random
import traceback
import sqlalchemy as sa
from datetime import datetime

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db

def add_to_pipelines():
    """Add contacts to various pipelines using raw SQL."""
    try:
        # Create Flask app context
        app = create_app()
        with app.app_context():
            # Print database info
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
                print(f"Database path: {db_path}")
                print(f"Database file exists: {os.path.exists(db_path)}")
                print(f"Database file size: {os.path.getsize(db_path) if os.path.exists(db_path) else 'N/A'} bytes")
            
            print("Adding contacts to pipelines...")
            
            # First, check if pipeline_contacts has any existing records
            existing_count = db.session.execute(sa.text("SELECT COUNT(*) FROM pipeline_contacts;")).scalar()
            if existing_count > 0:
                print(f"Found {existing_count} existing pipeline contacts. Clearing table first...")
                db.session.execute(sa.text("DELETE FROM pipeline_contacts;"))
                db.session.commit()
                print("Cleared existing pipeline contacts.")
            
            # Check the pipeline_contacts table schema
            print("Checking database schema...")
            schema_result = db.session.execute(sa.text("PRAGMA table_info(pipeline_contacts);")).fetchall()
            print("Pipeline_contacts columns:")
            column_names = []
            for col in schema_result:
                column_names.append(col[1])  # Column name is at index 1
                print(f"  - {col[1]} ({col[2]})")
            
            # Check for expected column names
            timestamp_columns = []
            if 'entered_at' in column_names:
                timestamp_columns.append('entered_at')
            elif 'created_at' in column_names:
                timestamp_columns.append('created_at')
            
            update_columns = []
            if 'last_updated' in column_names:
                update_columns.append('last_updated')
            elif 'updated_at' in column_names:
                update_columns.append('updated_at')
            
            if not timestamp_columns or not update_columns:
                print("Error: Could not determine timestamp column names in pipeline_contacts table")
                return
            
            timestamp_col = timestamp_columns[0]
            update_col = update_columns[0]
            print(f"Using timestamp columns: {timestamp_col}, {update_col}")
            
            # Get all pipelines
            pipelines = db.session.execute(sa.text("""
                SELECT id, name, pipeline_type, office_id FROM pipelines
            """)).fetchall()
            
            if not pipelines:
                print("No pipelines found in database.")
                return
            
            print(f"Found {len(pipelines)} pipelines")
            
            # Get pipeline stages - using 'order' instead of 'position'
            stages = db.session.execute(sa.text("""
                SELECT id, pipeline_id, name, "order" FROM pipeline_stages
                ORDER BY pipeline_id, "order" ASC
            """)).fetchall()
            
            if not stages:
                print("No pipeline stages found in database.")
                return
                
            print(f"Found {len(stages)} total pipeline stages")
            
            # Create mapping of pipeline_id to first stage_id
            pipeline_first_stages = {}
            for stage in stages:
                stage_id, pipeline_id = stage[0], stage[1]
                if pipeline_id not in pipeline_first_stages:
                    pipeline_first_stages[pipeline_id] = stage_id
            
            # Verify we have first stages for each pipeline
            for pipeline in pipelines:
                pipeline_id = pipeline[0]
                if pipeline_id not in pipeline_first_stages:
                    print(f"Warning: No stages found for pipeline ID {pipeline_id}")
            
            total_added = 0
            
            # Process by pipeline type
            for pipeline in pipelines:
                pipeline_id, name, pipeline_type, office_id = pipeline[0], pipeline[1], pipeline[2], pipeline[3]
                
                if pipeline_id not in pipeline_first_stages:
                    print(f"No stages found for pipeline {name} (ID: {pipeline_id}). Skipping...")
                    continue
                
                first_stage_id = pipeline_first_stages[pipeline_id]
                
                if pipeline_type == 'people' or pipeline_type == 'person':
                    # Get people - without office filtering, but ensure the contacts table has type='person'
                    people = db.session.execute(sa.text(f"""
                        SELECT c.id FROM contacts c 
                        WHERE c.type = 'person' AND c.office_id = {office_id}
                        LIMIT 10
                    """)).fetchall()
                    
                    people_ids = [p[0] for p in people]
                    print(f"Found {len(people_ids)} people for {name}")
                    
                    # Add people to this pipeline
                    added_count = 0
                    for contact_id in people_ids:
                        # Check if contact already in pipeline
                        existing = db.session.execute(sa.text(f"""
                            SELECT id FROM pipeline_contacts
                            WHERE pipeline_id = {pipeline_id} AND contact_id = {contact_id}
                        """)).fetchone()
                        
                        if not existing:
                            try:
                                # Add to pipeline
                                now = datetime.utcnow().isoformat()
                                insert_sql = f"""
                                    INSERT INTO pipeline_contacts
                                    (pipeline_id, contact_id, current_stage_id, {timestamp_col}, {update_col})
                                    VALUES ({pipeline_id}, {contact_id}, {first_stage_id}, '{now}', '{now}')
                                """
                                print(f"Executing SQL: {insert_sql}")
                                db.session.execute(sa.text(insert_sql))
                                added_count += 1
                                total_added += 1
                            except Exception as e:
                                print(f"Error adding contact {contact_id} to pipeline: {str(e)}")
                                db.session.rollback()
                                # Try to get more info about the error
                                print("Contact info:")
                                contact_info = db.session.execute(sa.text(f"SELECT * FROM contacts WHERE id = {contact_id}")).fetchone()
                                print(f"Contact data: {contact_info}")
                                print("Pipeline stage info:")
                                stage_info = db.session.execute(sa.text(f"SELECT * FROM pipeline_stages WHERE id = {first_stage_id}")).fetchone()
                                print(f"Stage data: {stage_info}")
                                continue
                    
                    # Commit after each pipeline batch
                    try:
                        db.session.commit()
                        print(f"Committed {added_count} people to {name}")
                    except Exception as e:
                        print(f"Error committing people to pipeline {pipeline_id}: {str(e)}")
                        db.session.rollback()
                
                elif pipeline_type == 'church':
                    # Get churches - filter by type and office_id
                    churches = db.session.execute(sa.text(f"""
                        SELECT c.id FROM contacts c 
                        WHERE c.type = 'church' AND c.office_id = {office_id}
                        LIMIT 10
                    """)).fetchall()
                    
                    church_ids = [c[0] for c in churches]
                    print(f"Found {len(church_ids)} churches for {name}")
                    
                    # Add churches to this pipeline
                    added_count = 0
                    for contact_id in church_ids:
                        # Check if contact already in pipeline
                        existing = db.session.execute(sa.text(f"""
                            SELECT id FROM pipeline_contacts
                            WHERE pipeline_id = {pipeline_id} AND contact_id = {contact_id}
                        """)).fetchone()
                        
                        if not existing:
                            try:
                                # Add to pipeline
                                now = datetime.utcnow().isoformat()
                                insert_sql = f"""
                                    INSERT INTO pipeline_contacts
                                    (pipeline_id, contact_id, current_stage_id, {timestamp_col}, {update_col})
                                    VALUES ({pipeline_id}, {contact_id}, {first_stage_id}, '{now}', '{now}')
                                """
                                print(f"Executing SQL: {insert_sql}")
                                db.session.execute(sa.text(insert_sql))
                                added_count += 1
                                total_added += 1
                            except Exception as e:
                                print(f"Error adding contact {contact_id} to pipeline: {str(e)}")
                                db.session.rollback()
                                continue
                    
                    # Commit after each pipeline batch
                    try:
                        db.session.commit()
                        print(f"Committed {added_count} churches to {name}")
                    except Exception as e:
                        print(f"Error committing churches to pipeline {pipeline_id}: {str(e)}")
                        db.session.rollback()
            
            # Final commit to ensure all changes are saved
            try:
                db.session.commit()
                print(f"\nTotal contacts added to pipelines: {total_added}")
            except Exception as e:
                print(f"Error in final commit: {str(e)}")
                db.session.rollback()
            
            # Verify pipeline counts
            print("\nVerifying pipeline counts...")
            people_count = db.session.execute(sa.text("""
                SELECT COUNT(*) FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                WHERE c.type = 'person'
            """)).scalar()
            
            churches_count = db.session.execute(sa.text("""
                SELECT COUNT(*) FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                WHERE c.type = 'church'
            """)).scalar()
            
            pipeline_total = db.session.execute(sa.text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
            
            print(f"Final counts:")
            print(f"Total pipeline_contacts: {pipeline_total}")
            print(f"People in pipelines: {people_count}")
            print(f"Churches in pipelines: {churches_count}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        traceback.print_exc()
        # Only try to rollback if we have an application context
        try:
            db.session.rollback()
        except:
            pass

if __name__ == "__main__":
    add_to_pipelines() 