from app import create_app
from app.models.pipeline import Pipeline, PipelineStage, PipelineContact
from app.models.church import Church
from app.models.contact import Contact
from app.extensions import db
from datetime import datetime
from sqlalchemy import text
import time
import os
import sys
import sqlite3

def fix_church_pipeline():
    """Check and fix the church pipeline to ensure all churches are correctly added."""
    app = create_app()
    
    # Verify the database path
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_path:
        print("Database URI not found in app config!")
        return
        
    print(f"App configured database: {db_path}")
    
    # Extract the actual file path for SQLite database
    sqlite_path = None
    if db_path.startswith('sqlite:///'):
        sqlite_path = db_path[10:]
        if not sqlite_path.startswith('/'):
            # Relative path
            sqlite_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), sqlite_path)
    
    if sqlite_path:
        print(f"SQLite database path: {sqlite_path}")
        if not os.path.exists(sqlite_path):
            print(f"WARNING: SQLite database file does not exist at {sqlite_path}")
        else:
            print(f"Database file exists, size: {os.path.getsize(sqlite_path)} bytes")
    
    with app.app_context():
        try:
            # Try to make a direct SQLite connection to verify
            if sqlite_path and os.path.exists(sqlite_path):
                try:
                    direct_conn = sqlite3.connect(sqlite_path)
                    direct_cursor = direct_conn.cursor()
                    direct_cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
                    count = direct_cursor.fetchone()[0]
                    print(f"Direct SQLite connection: {count} total pipeline contacts")
                    direct_conn.close()
                except Exception as e:
                    print(f"Error with direct SQLite connection: {str(e)}")
            
            # Print the SQLAlchemy connection URL info
            db_url = str(db.engine.url)
            # Mask password if present
            if '@' in db_url:
                db_url = db_url.split('@')[1]
            print(f"Database connection: {db_url}")
            
            # Get app config info
            print(f"Debug mode: {app.debug}")
            print(f"Testing mode: {app.testing}")
            print(f"DB path: {os.path.abspath(app.config.get('SQLALCHEMY_DATABASE_URI', 'Not found'))}")
            
            # Check SQLAlchemy connection
            test_count = db.session.execute(text("SELECT COUNT(*) FROM pipeline_contacts")).scalar()
            print(f"SQLAlchemy test query: {test_count} total pipeline contacts")
            
            # Get the main church pipeline
            church_pipeline = Pipeline.query.filter_by(
                pipeline_type='church',
                is_main_pipeline=True,
                office_id=1  # Main Office
            ).first()
            
            if not church_pipeline:
                print("Main church pipeline not found")
                return
                
            print(f"Found main church pipeline: {church_pipeline.name} (ID: {church_pipeline.id})")
            
            # Get the stages for this pipeline
            stages = PipelineStage.query.filter_by(pipeline_id=church_pipeline.id).order_by(PipelineStage.order).all()
            if not stages:
                print("No stages found for church pipeline")
                return
                
            # Create a dictionary of stage names to stages
            stage_dict = {stage.name: stage for stage in stages}
            default_stage = stage_dict.get("INFORMATION") or stages[0]
            
            print(f"Default stage: {default_stage.name} (ID: {default_stage.id})")
            
            # Check the contacts in pipeline directly using SQL
            pre_check = db.session.execute(
                text("SELECT id, contact_id, current_stage_id FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
                {"pipeline_id": church_pipeline.id}
            ).fetchall()
            print(f"PRE-CHECK: Found {len(pre_check)} contacts in pipeline via direct SQL")
            print(f"PRE-CHECK: Contact IDs: {[row[1] for row in pre_check]}")
            
            # Get all churches
            churches = Church.query.all()
            print(f"Found {len(churches)} churches in database")
            
            # Count churches already in pipeline
            existing_contacts = db.session.query(PipelineContact.contact_id).filter(
                PipelineContact.pipeline_id == church_pipeline.id
            ).all()
            existing_contact_ids = [contact[0] for contact in existing_contacts]
            print(f"Found {len(existing_contact_ids)} churches already in pipeline")
            print(f"Existing contact IDs: {existing_contact_ids}")
            
            # Get Contact IDs for churches
            church_contact_ids = []
            for church in churches:
                # Check if there's a corresponding Contact record
                contact = Contact.query.filter_by(id=church.id).first()
                if contact:
                    church_contact_ids.append(contact.id)
            
            print(f"Found {len(church_contact_ids)} church contact IDs")
            print(f"Church contact IDs: {church_contact_ids}")
            
            # Find churches not in the pipeline
            missing_ids = set(church_contact_ids) - set(existing_contact_ids)
            print(f"Found {len(missing_ids)} churches missing from pipeline")
            print(f"Missing IDs: {missing_ids}")
            
            # Reset the session to ensure clean state
            db.session.close()
            db.session = db.create_scoped_session()
            
            # Add missing churches to pipeline
            count = 0
            batch_size = 5
            batch_count = 0
            
            # Create a fresh connection for direct verification
            if sqlite_path and os.path.exists(sqlite_path):
                verify_conn = sqlite3.connect(sqlite_path)
                verify_cursor = verify_conn.cursor()
            
            for contact_id in missing_ids:
                try:
                    # Check if this contact already exists in pipeline first
                    existing = db.session.execute(
                        text("SELECT id FROM pipeline_contacts WHERE pipeline_id = :pipeline_id AND contact_id = :contact_id"),
                        {"pipeline_id": church_pipeline.id, "contact_id": contact_id}
                    ).fetchone()
                    
                    if existing:
                        print(f"SKIP: Contact ID {contact_id} already exists in pipeline (ID: {existing[0]})")
                        continue
                        
                    # Create pipeline contact
                    pipeline_contact = PipelineContact(
                        pipeline_id=church_pipeline.id,
                        contact_id=contact_id,
                        current_stage_id=default_stage.id,
                        entered_at=datetime.now(),
                        last_updated=datetime.now()
                    )
                    
                    db.session.add(pipeline_contact)
                    db.session.flush()  # Flush to get the ID without committing
                    print(f"Added contact ID {contact_id} to pipeline (uncommitted ID: {pipeline_contact.id})")
                    
                    count += 1
                    batch_count += 1
                    
                    # Commit in small batches
                    if batch_count >= batch_size:
                        db.session.commit()
                        db.session.close()  # Close session to release resources
                        db.session = db.create_scoped_session()  # Create a new session
                        print(f"Committed batch of {batch_count} contacts")
                        
                        # Force SQLite to sync to disk
                        if sqlite_path and os.path.exists(sqlite_path):
                            try:
                                verify_cursor.execute("PRAGMA wal_checkpoint;")
                                verify_conn.commit()
                            except Exception as e:
                                print(f"Error running checkpoint: {str(e)}")
                        
                        batch_count = 0
                        time.sleep(0.1)  # Small pause between batches
                    
                except Exception as e:
                    print(f"Error adding contact ID {contact_id}: {str(e)}")
                    db.session.rollback()
            
            # Commit final batch
            if batch_count > 0:
                db.session.commit()
                print(f"Committed final batch of {batch_count} contacts")
                
                # Force SQLite to sync to disk
                if sqlite_path and os.path.exists(sqlite_path):
                    try:
                        verify_cursor.execute("PRAGMA wal_checkpoint;")
                        verify_conn.commit()
                    except Exception as e:
                        print(f"Error running checkpoint: {str(e)}")
            
            # Close the verification connection
            if sqlite_path and os.path.exists(sqlite_path):
                verify_conn.close()
                
            print(f"Added {count} churches to main pipeline")
            
            # Verify the contacts were added
            print("Verifying contacts were added...")
            time.sleep(1)  # Give the database a moment to process
            
            # Check the contacts in pipeline directly using SQL again
            post_check = db.session.execute(
                text("SELECT id, contact_id, current_stage_id FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
                {"pipeline_id": church_pipeline.id}
            ).fetchall()
            print(f"POST-CHECK: Found {len(post_check)} contacts in pipeline via direct SQL")
            print(f"POST-CHECK: Contact IDs: {[row[1] for row in post_check]}")
            
            # Count churches in pipeline again
            updated_contacts = db.session.query(PipelineContact.contact_id).filter(
                PipelineContact.pipeline_id == church_pipeline.id
            ).all()
            updated_contact_ids = [contact[0] for contact in updated_contacts]
            print(f"After fix: Found {len(updated_contact_ids)} churches in pipeline")
            print(f"After fix: Contact IDs: {updated_contact_ids}")
            
            # Direct SQL query to check
            raw_count = db.session.execute(
                text("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = :pipeline_id"),
                {"pipeline_id": church_pipeline.id}
            ).scalar() or 0
            print(f"Raw SQL count of pipeline contacts: {raw_count}")
            
            # Try to run VACUUM to optimize the database
            try:
                db.session.execute(text("VACUUM;"))
                print("Ran VACUUM on database")
            except Exception as e:
                print(f"Error running VACUUM: {str(e)}")
        
        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
        
if __name__ == "__main__":
    fix_church_pipeline() 