#!/usr/bin/env python3
"""
Script to directly fix pipeline contacts by writing to the database file.
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def fix_pipeline_contacts():
    """Fix pipeline contacts by directly writing to the database."""
    print("Fixing pipeline contacts by writing directly to the database...")
    
    try:
        # Directly connect to the database file
        db_path = project_root / "instance" / "mobilize_crm.db"
        
        if not db_path.exists():
            print(f"❌ Database file not found at {db_path}")
            return
        
        print(f"Using database at: {db_path}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check the tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in database: {[t[0] for t in tables]}")
        
        # Check if table exists
        if ('pipeline_contacts',) not in tables:
            print("❌ pipeline_contacts table not found in database")
            return
        
        # First, check if any existing pipeline contacts
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts;")
        count = cursor.fetchone()[0]
        print(f"Current pipeline_contacts count: {count}")
        
        # Clear existing pipeline contacts
        cursor.execute("DELETE FROM pipeline_contacts;")
        conn.commit()
        print("Cleared existing pipeline contacts")
        
        # Get all people
        cursor.execute("SELECT id, office_id FROM contacts WHERE type = 'person';")
        people = cursor.fetchall()
        print(f"Found {len(people)} people")
        
        # Get all churches
        cursor.execute("SELECT id, office_id FROM contacts WHERE type = 'church';")
        churches = cursor.fetchall()
        print(f"Found {len(churches)} churches")
        
        # Get pipelines
        cursor.execute("SELECT id, office_id, pipeline_type FROM pipelines;")
        pipelines = cursor.fetchall()
        print(f"Found {len(pipelines)} pipelines")
        
        # Group pipelines by office and type
        pipeline_map = {}
        for p_id, office_id, p_type in pipelines:
            key = (office_id, p_type)
            if key not in pipeline_map:
                pipeline_map[key] = []
            pipeline_map[key].append(p_id)
        
        # Get first stages for each pipeline
        pipeline_stages = {}
        for p_id, _, _ in pipelines:
            cursor.execute(
                "SELECT id FROM pipeline_stages WHERE pipeline_id = ? ORDER BY \"order\" ASC LIMIT 1;", 
                (p_id,)
            )
            stage = cursor.fetchone()
            if stage:
                pipeline_stages[p_id] = stage[0]
        
        # Add people to pipelines (about 30% of people)
        added_people = 0
        for person_id, office_id in people:
            if random.random() < 0.3:
                # Find pipeline for this office
                key = (office_id, 'people')
                if key in pipeline_map and pipeline_map[key]:
                    pipeline_id = random.choice(pipeline_map[key])
                    
                    if pipeline_id in pipeline_stages:
                        stage_id = pipeline_stages[pipeline_id]
                        
                        # Insert directly
                        entered_at = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                        last_updated = (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
                        
                        cursor.execute(
                            """
                            INSERT INTO pipeline_contacts 
                            (contact_id, pipeline_id, current_stage_id, entered_at, last_updated)
                            VALUES (?, ?, ?, ?, ?);
                            """,
                            (person_id, pipeline_id, stage_id, entered_at, last_updated)
                        )
                        added_people += 1
                        print(f"Added person {person_id} to pipeline {pipeline_id}")
        
        # Add churches to pipelines (about 30% of churches)
        added_churches = 0
        for church_id, office_id in churches:
            if random.random() < 0.3:
                # Find pipeline for this office
                key = (office_id, 'church')
                if key in pipeline_map and pipeline_map[key]:
                    pipeline_id = random.choice(pipeline_map[key])
                    
                    if pipeline_id in pipeline_stages:
                        stage_id = pipeline_stages[pipeline_id]
                        
                        # Insert directly
                        entered_at = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                        last_updated = (datetime.now() - timedelta(days=random.randint(0, 5))).isoformat()
                        
                        cursor.execute(
                            """
                            INSERT INTO pipeline_contacts 
                            (contact_id, pipeline_id, current_stage_id, entered_at, last_updated)
                            VALUES (?, ?, ?, ?, ?);
                            """,
                            (church_id, pipeline_id, stage_id, entered_at, last_updated)
                        )
                        added_churches += 1
                        print(f"Added church {church_id} to pipeline {pipeline_id}")
        
        # Commit all changes
        conn.commit()
        
        # Verify the new count
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts;")
        new_count = cursor.fetchone()[0]
        print(f"✅ New pipeline_contacts count: {new_count}")
        print(f"Added {added_people} people and {added_churches} churches to pipelines")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error fixing pipeline contacts: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    fix_pipeline_contacts() 