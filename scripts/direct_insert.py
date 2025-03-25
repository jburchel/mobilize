#!/usr/bin/env python
"""Direct insert script without Flask."""
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Database path
DB_PATH = Path("instance/mobilize_crm.db")

def check_database_state(cursor):
    """Check database state, triggers, and constraints."""
    print("\n=== Database State Check ===")
    
    # Check journal mode
    cursor.execute("PRAGMA journal_mode;")
    journal_mode = cursor.fetchone()[0]
    print(f"Journal mode: {journal_mode}")
    
    # Check synchronous setting
    cursor.execute("PRAGMA synchronous;")
    synchronous = cursor.fetchone()[0]
    print(f"Synchronous setting: {synchronous}")
    
    # Check foreign keys status
    cursor.execute("PRAGMA foreign_keys;")
    foreign_keys = cursor.fetchone()[0]
    print(f"Foreign keys enabled: {foreign_keys}")
    
    # List all triggers
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='trigger';")
    triggers = cursor.fetchall()
    if triggers:
        print("\nTriggers found:")
        for trigger in triggers:
            print(f"  - {trigger[0]}:")
            print(f"    {trigger[1]}")
    else:
        print("\nNo triggers found")
    
    # Check foreign key constraints
    print("\nForeign key constraints:")
    tables = ['pipeline_contacts', 'contacts', 'pipelines', 'pipeline_stages']
    for table in tables:
        cursor.execute(f"PRAGMA foreign_key_list('{table}');")
        constraints = cursor.fetchall()
        if constraints:
            print(f"\n  {table} constraints:")
            for constraint in constraints:
                print(f"    - References {constraint[2]}({constraint[3]}) from column {constraint[4]}")

def verify_data_integrity(cursor):
    """Verify data integrity before insertion."""
    print("\n=== Data Integrity Check ===")
    
    # Check pipeline stages exist
    cursor.execute("SELECT COUNT(*) FROM pipeline_stages;")
    stages_count = cursor.fetchone()[0]
    print(f"Pipeline stages count: {stages_count}")
    
    # Check contacts exist
    cursor.execute("SELECT COUNT(*) FROM contacts;")
    contacts_count = cursor.fetchone()[0]
    print(f"Contacts count: {contacts_count}")
    
    # Check pipelines exist
    cursor.execute("SELECT COUNT(*) FROM pipelines;")
    pipelines_count = cursor.fetchone()[0]
    print(f"Pipelines count: {pipelines_count}")
    
    # Sample check for data consistency
    cursor.execute("""
        SELECT p.id, p.name, COUNT(ps.id) as stage_count
        FROM pipelines p
        LEFT JOIN pipeline_stages ps ON p.id = ps.pipeline_id
        GROUP BY p.id, p.name;
    """)
    pipeline_stats = cursor.fetchall()
    print("\nPipeline statistics:")
    for stat in pipeline_stats:
        print(f"  Pipeline {stat[0]} ({stat[1]}) has {stat[2]} stages")

def direct_insert():
    """Insert directly into the database using sqlite3."""
    print(f"Database path: {DB_PATH.absolute()}")
    print(f"Database exists: {DB_PATH.exists()}")
    
    if not DB_PATH.exists():
        print("Error: Database file not found!")
        return
    
    try:
        # Connect to the database with immediate transaction mode
        conn = sqlite3.connect(str(DB_PATH), isolation_level='IMMEDIATE')
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Check database state
        check_database_state(cursor)
        
        # Verify data integrity
        verify_data_integrity(cursor)
        
        # Check the current count
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        count_before = cursor.fetchone()[0]
        print(f"\nPipeline contacts before: {count_before}")
        
        # Delete any existing pipeline contacts
        cursor.execute("DELETE FROM pipeline_contacts")
        conn.commit()
        print("Deleted all existing pipeline contacts")
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        count_after_delete = cursor.fetchone()[0]
        print(f"Pipeline contacts after deletion: {count_after_delete}")
        
        # Get all pipelines
        cursor.execute("SELECT id, name, pipeline_type, office_id FROM pipelines")
        pipelines = cursor.fetchall()
        print(f"\nFound {len(pipelines)} pipelines")
        
        # Process pipelines
        total_added = 0
        
        for pipeline in pipelines:
            pipeline_id, name, pipeline_type, office_id = pipeline
            
            # Get the first stage for this pipeline
            cursor.execute("""
                SELECT id, name
                FROM pipeline_stages
                WHERE pipeline_id = ?
                ORDER BY "order"
                LIMIT 1
            """, (pipeline_id,))
            first_stage = cursor.fetchone()
            
            if not first_stage:
                print(f"No stages found for pipeline {name} (ID: {pipeline_id}). Skipping...")
                continue
            
            first_stage_id, first_stage_name = first_stage
            print(f"\nProcessing pipeline: {name}")
            print(f"First stage: {first_stage_name} (ID: {first_stage_id})")
            
            # Get contacts based on pipeline type
            if pipeline_type == 'people' or pipeline_type == 'person':
                cursor.execute(
                    "SELECT c.id FROM contacts c WHERE c.type = 'person' AND c.office_id = ? LIMIT 10",
                    (office_id,)
                )
                people = cursor.fetchall()
                people_ids = [p[0] for p in people]
                print(f"Found {len(people_ids)} people for {name}")
                
                # Add people to pipeline
                added_count = 0
                for contact_id in people_ids:
                    try:
                        # Check if contact exists
                        cursor.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,))
                        if not cursor.fetchone():
                            print(f"Warning: Contact {contact_id} does not exist")
                            continue
                        
                        # Check if stage exists
                        cursor.execute("SELECT id FROM pipeline_stages WHERE id = ?", (first_stage_id,))
                        if not cursor.fetchone():
                            print(f"Warning: Stage {first_stage_id} does not exist")
                            continue
                        
                        # Check if already exists
                        cursor.execute(
                            "SELECT id FROM pipeline_contacts WHERE pipeline_id = ? AND contact_id = ?",
                            (pipeline_id, contact_id)
                        )
                        existing = cursor.fetchone()
                        
                        if not existing:
                            now = datetime.utcnow().isoformat()
                            cursor.execute(
                                "INSERT INTO pipeline_contacts (pipeline_id, contact_id, current_stage_id, entered_at, last_updated) VALUES (?, ?, ?, ?, ?)",
                                (pipeline_id, contact_id, first_stage_id, now, now)
                            )
                            added_count += 1
                            total_added += 1
                    except sqlite3.Error as e:
                        print(f"Error adding person {contact_id} to pipeline: {e}")
                        continue
                
                print(f"Added {added_count} people to pipeline {name}")
                
                # Commit after each pipeline to ensure data is saved
                conn.commit()
                print(f"Committed changes for pipeline {name}")
                
                # Verify the insertion immediately
                cursor.execute(
                    "SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = ?",
                    (pipeline_id,)
                )
                verify_count = cursor.fetchone()[0]
                print(f"Verification: {verify_count} contacts in pipeline {name} immediately after commit")
            
            elif pipeline_type == 'church':
                cursor.execute(
                    "SELECT c.id FROM contacts c WHERE c.type = 'church' AND c.office_id = ? LIMIT 10",
                    (office_id,)
                )
                churches = cursor.fetchall()
                church_ids = [c[0] for c in churches]
                print(f"Found {len(church_ids)} churches for {name}")
                
                # Add churches to pipeline
                added_count = 0
                for contact_id in church_ids:
                    try:
                        # Check if contact exists
                        cursor.execute("SELECT id FROM contacts WHERE id = ?", (contact_id,))
                        if not cursor.fetchone():
                            print(f"Warning: Contact {contact_id} does not exist")
                            continue
                        
                        # Check if stage exists
                        cursor.execute("SELECT id FROM pipeline_stages WHERE id = ?", (first_stage_id,))
                        if not cursor.fetchone():
                            print(f"Warning: Stage {first_stage_id} does not exist")
                            continue
                        
                        # Check if already exists
                        cursor.execute(
                            "SELECT id FROM pipeline_contacts WHERE pipeline_id = ? AND contact_id = ?",
                            (pipeline_id, contact_id)
                        )
                        existing = cursor.fetchone()
                        
                        if not existing:
                            now = datetime.utcnow().isoformat()
                            cursor.execute(
                                "INSERT INTO pipeline_contacts (pipeline_id, contact_id, current_stage_id, entered_at, last_updated) VALUES (?, ?, ?, ?, ?)",
                                (pipeline_id, contact_id, first_stage_id, now, now)
                            )
                            added_count += 1
                            total_added += 1
                    except sqlite3.Error as e:
                        print(f"Error adding church {contact_id} to pipeline: {e}")
                        continue
                
                print(f"Added {added_count} churches to pipeline {name}")
                
                # Commit after each pipeline to ensure data is saved
                conn.commit()
                print(f"Committed changes for pipeline {name}")
                
                # Verify the insertion immediately
                cursor.execute(
                    "SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = ?",
                    (pipeline_id,)
                )
                verify_count = cursor.fetchone()[0]
                print(f"Verification: {verify_count} contacts in pipeline {name} immediately after commit")
        
        # Final commit to ensure all changes are saved
        conn.commit()
        print("Final commit completed")
        
        # Verify counts
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        count_after = cursor.fetchone()[0]
        print(f"\nPipeline contacts after all operations: {count_after}")
        print(f"Difference: {count_after - count_before}")
        
        # Sleep to make sure everything is flushed to disk
        print("Waiting 2 seconds to ensure data is flushed to disk...")
        time.sleep(2)
        
        # Check one more time
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        final_count = cursor.fetchone()[0]
        print(f"Final count check: {final_count} pipeline contacts")
        
        # Show some sample records
        if final_count > 0:
            cursor.execute("""
                SELECT pc.*, c.first_name || ' ' || c.last_name as contact_name, 
                       p.name as pipeline_name, ps.name as stage_name
                FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                JOIN pipelines p ON pc.pipeline_id = p.id
                JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                LIMIT 5
            """)
            samples = cursor.fetchall()
            print("\nSample records:")
            for sample in samples:
                print(f"  {sample}")
        
        # Open a new connection to verify persistence
        print("\nVerifying with a new connection...")
        conn.close()
        
        new_conn = sqlite3.connect(str(DB_PATH))
        new_cursor = new_conn.cursor()
        new_cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        new_conn_count = new_cursor.fetchone()[0]
        print(f"Count from new connection: {new_conn_count}")
        
        if new_conn_count > 0:
            new_cursor.execute("""
                SELECT pc.*, c.first_name || ' ' || c.last_name as contact_name,
                       p.name as pipeline_name, ps.name as stage_name
                FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                JOIN pipelines p ON pc.pipeline_id = p.id
                JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                LIMIT 5
            """)
            new_samples = new_cursor.fetchall()
            print("Sample records from new connection:")
            for sample in new_samples:
                print(f"  {sample}")
            
            # Verify foreign key relationships
            print("\nVerifying foreign key relationships:")
            new_cursor.execute("""
                SELECT pc.id, pc.contact_id, pc.pipeline_id, pc.current_stage_id,
                       c.id as contact_exists, p.id as pipeline_exists, ps.id as stage_exists
                FROM pipeline_contacts pc
                LEFT JOIN contacts c ON pc.contact_id = c.id
                LEFT JOIN pipelines p ON pc.pipeline_id = p.id
                LEFT JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                LIMIT 5;
            """)
            relationship_check = new_cursor.fetchall()
            for check in relationship_check:
                print(f"  Pipeline Contact {check[0]}:")
                print(f"    - Contact {check[1]} exists: {check[4] is not None}")
                print(f"    - Pipeline {check[2]} exists: {check[5] is not None}")
                print(f"    - Stage {check[3]} exists: {check[6] is not None}")
        
        new_conn.close()
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        if 'conn' in locals():
            conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    direct_insert() 