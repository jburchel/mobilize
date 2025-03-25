#!/usr/bin/env python3
"""
Script to fix pipeline contacts issues by enabling foreign keys and repopulating pipelines
"""
from app import create_app, db
from app.models import Pipeline, PipelineStage, PipelineContact, Contact, Person, Church, PipelineStageHistory, Office
from sqlalchemy import text
from datetime import datetime
import random
import sys
import traceback

app = create_app()

def enable_foreign_keys():
    """Enable foreign key constraints in SQLite"""
    with app.app_context():
        print("Enabling foreign key constraints...")
        try:
            # Check current status
            result = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
            print(f"Current foreign_keys setting: {result}")
            
            # Enable foreign keys
            db.session.execute(text("PRAGMA foreign_keys = ON;"))
            
            # Verify the change
            result = db.session.execute(text("PRAGMA foreign_keys;")).scalar()
            print(f"New foreign_keys setting: {result}")
            
            # Run integrity check
            integrity = db.session.execute(text("PRAGMA integrity_check;")).scalar()
            print(f"Database integrity: {integrity}")
            
            db.session.commit()
            print("Foreign key constraints enabled successfully.")
        except Exception as e:
            print(f"Error enabling foreign key constraints: {str(e)}")
            traceback.print_exc()
            db.session.rollback()

def clear_pipeline_contacts():
    """Clear existing pipeline contacts properly"""
    with app.app_context():
        print("Clearing existing pipeline contacts...")
        try:
            # Get count before deletion
            count = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
            print(f"Original pipeline contacts count: {count}")
            
            # Delete using raw SQL to avoid SQLAlchemy join issues
            result = db.session.execute(text("DELETE FROM pipeline_contacts"))
            db.session.commit()
            
            # Verify deletion
            count = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
            print(f"Pipeline contacts after deletion: {count}")
            
            print("Pipeline contacts cleared successfully.")
        except Exception as e:
            print(f"Error clearing pipeline contacts: {str(e)}")
            traceback.print_exc()
            db.session.rollback()

def add_pipeline_contacts_direct():
    """Add pipeline contacts using direct SQL for better control"""
    with app.app_context():
        print("Adding pipeline contacts using direct SQL...")
        
        # Get data needed for operation
        offices = Office.query.all()
        print(f"Found {len(offices)} offices in the database")
        
        # Process each office
        total_people_added = 0
        total_churches_added = 0
        
        for office in offices:
            print(f"\nProcessing Office: {office.name} (ID: {office.id})")
            
            # Get main pipelines for this office
            main_people_pipeline = Pipeline.query.filter_by(
                is_main_pipeline=True, 
                pipeline_type="people",
                office_id=office.id
            ).first()
            
            main_church_pipeline = Pipeline.query.filter_by(
                is_main_pipeline=True, 
                pipeline_type="church",
                office_id=office.id
            ).first()
            
            if not main_people_pipeline:
                print(f"No main people pipeline found for office {office.name}")
                continue
                
            if not main_church_pipeline:
                print(f"No main church pipeline found for office {office.name}")
                continue
            
            print(f"Found main people pipeline: {main_people_pipeline.name} (ID: {main_people_pipeline.id})")
            print(f"Found main church pipeline: {main_church_pipeline.name} (ID: {main_church_pipeline.id})")
            
            # Get stages for these pipelines
            people_stages = PipelineStage.query.filter_by(pipeline_id=main_people_pipeline.id).all()
            church_stages = PipelineStage.query.filter_by(pipeline_id=main_church_pipeline.id).all()
            
            print(f"Found {len(people_stages)} people stages and {len(church_stages)} church stages")
            
            if not people_stages or not church_stages:
                print("Missing stages for this office's pipelines")
                continue
            
            # Get people for this office
            office_people = Person.query.filter_by(office_id=office.id).all()
            print(f"Found {len(office_people)} people in {office.name}")
            
            # Add each person to the main people pipeline
            people_success = 0
            people_errors = 0
            
            for person in office_people:
                try:
                    # Get a random stage
                    random_stage = random.choice(people_stages)
                    
                    # Current timestamp
                    now = datetime.now().isoformat()
                    
                    # Insert pipeline contact using direct SQL
                    db.session.execute(text(f"""
                        INSERT INTO pipeline_contacts (contact_id, pipeline_id, current_stage_id, entered_at, last_updated)
                        VALUES ({person.id}, {main_people_pipeline.id}, {random_stage.id}, '{now}', '{now}')
                    """))
                    
                    # Get the ID of the inserted record
                    pc_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
                    
                    # Insert history entry
                    db.session.execute(text(f"""
                        INSERT INTO pipeline_stage_history (pipeline_contact_id, to_stage_id, created_by_id, notes, created_at)
                        VALUES ({pc_id}, {random_stage.id}, 1, 'Initial stage assignment', '{now}')
                    """))
                    
                    # Commit each record individually to avoid transaction issues
                    db.session.commit()
                    people_success += 1
                    total_people_added += 1
                    
                    if people_success % 5 == 0:
                        print(f"  Added {people_success} people to {main_people_pipeline.name}")
                        
                except Exception as e:
                    people_errors += 1
                    print(f"Error adding person ID {person.id} to pipeline {main_people_pipeline.id}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
            
            print(f"Office {office.name} - People success: {people_success}, errors: {people_errors}")
            
            # Get churches for this office
            office_churches = Church.query.filter_by(office_id=office.id).all()
            print(f"Found {len(office_churches)} churches in {office.name}")
            
            # Add each church to the main church pipeline
            church_success = 0
            church_errors = 0
            
            for church in office_churches:
                try:
                    # Get a random stage
                    random_stage = random.choice(church_stages)
                    
                    # Current timestamp
                    now = datetime.now().isoformat()
                    
                    # Insert pipeline contact using direct SQL
                    db.session.execute(text(f"""
                        INSERT INTO pipeline_contacts (contact_id, pipeline_id, current_stage_id, entered_at, last_updated)
                        VALUES ({church.id}, {main_church_pipeline.id}, {random_stage.id}, '{now}', '{now}')
                    """))
                    
                    # Get the ID of the inserted record
                    pc_id = db.session.execute(text("SELECT last_insert_rowid()")).scalar()
                    
                    # Insert history entry
                    db.session.execute(text(f"""
                        INSERT INTO pipeline_stage_history (pipeline_contact_id, to_stage_id, created_by_id, notes, created_at)
                        VALUES ({pc_id}, {random_stage.id}, 1, 'Initial stage assignment', '{now}')
                    """))
                    
                    # Commit each record individually to avoid transaction issues
                    db.session.commit()
                    church_success += 1
                    total_churches_added += 1
                    
                    if church_success % 5 == 0:
                        print(f"  Added {church_success} churches to {main_church_pipeline.name}")
                        
                except Exception as e:
                    church_errors += 1
                    print(f"Error adding church ID {church.id} to pipeline {main_church_pipeline.id}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
            
            print(f"Office {office.name} - Churches success: {church_success}, errors: {church_errors}")
        
        # Verify final counts
        final_count = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
        print(f"\nTotal contacts added: {total_people_added + total_churches_added}")
        print(f"Final pipeline_contacts count in database: {final_count}")

def verify_pipeline_contacts():
    """Verify that pipeline contacts were added correctly"""
    with app.app_context():
        print("\nVerifying pipeline contacts:")
        
        # Get counts per pipeline
        result = db.session.execute(text("""
            SELECT p.id, p.name, p.pipeline_type, p.is_main_pipeline, COUNT(pc.id) as contacts
            FROM pipelines p
            LEFT JOIN pipeline_contacts pc ON p.id = pc.pipeline_id
            WHERE p.is_main_pipeline = 1
            GROUP BY p.id
            ORDER BY p.id
        """))
        
        for row in result:
            print(f"Pipeline {row.name} (ID: {row.id}, Type: {row.pipeline_type}): {row.contacts} contacts")
        
        # Get overall counts
        people_count = db.session.execute(text("""
            SELECT COUNT(pc.id) 
            FROM pipeline_contacts pc
            JOIN pipelines p ON pc.pipeline_id = p.id
            JOIN contacts c ON pc.contact_id = c.id
            WHERE p.is_main_pipeline = 1 AND c.type = 'person'
        """)).scalar()
        
        church_count = db.session.execute(text("""
            SELECT COUNT(pc.id) 
            FROM pipeline_contacts pc
            JOIN pipelines p ON pc.pipeline_id = p.id
            JOIN contacts c ON pc.contact_id = c.id
            WHERE p.is_main_pipeline = 1 AND c.type = 'church'
        """)).scalar()
        
        print(f"\nTotal people in main pipelines: {people_count}")
        print(f"Total churches in main pipelines: {church_count}")
        print(f"Total contacts in main pipelines: {people_count + church_count}")

if __name__ == "__main__":
    # First, enable foreign keys
    enable_foreign_keys()
    
    # Then clear existing pipeline contacts
    clear_pipeline_contacts()
    
    # Add pipeline contacts using direct SQL
    add_pipeline_contacts_direct()
    
    # Verify the results
    verify_pipeline_contacts()
    
    print("\nPipeline contacts fix completed. Please run check_pipelines.py to verify all is working correctly.")
    sys.exit(0) 