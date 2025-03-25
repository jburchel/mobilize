#!/usr/bin/env python
"""Check counts in the database."""
import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path("instance/mobilize_crm.db")

def check_counts():
    """Check counts in the database using direct SQLite access."""
    print(f"Database path: {DB_PATH.absolute()}")
    print(f"Database exists: {DB_PATH.exists()}")
    
    if not DB_PATH.exists():
        print("Error: Database file not found!")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Check database state
        print("\n=== Database State ===")
        cursor.execute("PRAGMA journal_mode;")
        print(f"Journal mode: {cursor.fetchone()[0]}")
        
        cursor.execute("PRAGMA synchronous;")
        print(f"Synchronous setting: {cursor.fetchone()[0]}")
        
        cursor.execute("PRAGMA foreign_keys;")
        print(f"Foreign keys enabled: {cursor.fetchone()[0]}")
        
        # Get total counts
        print("\n=== Total Counts ===")
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'person'")
        people_count = cursor.fetchone()[0]
        print(f"Total people in contacts: {people_count}")
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'church'")
        church_count = cursor.fetchone()[0]
        print(f"Total churches in contacts: {church_count}")
        
        cursor.execute("SELECT COUNT(*) FROM pipeline_contacts")
        pipeline_contacts_count = cursor.fetchone()[0]
        print(f"Total pipeline contacts: {pipeline_contacts_count}")
        
        # Get pipeline details
        print("\n=== Pipeline Details ===")
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.pipeline_type,
                o.name as office_name,
                COUNT(DISTINCT pc.contact_id) as contact_count,
                COUNT(DISTINCT ps.id) as stage_count
            FROM pipelines p
            LEFT JOIN offices o ON p.office_id = o.id
            LEFT JOIN pipeline_contacts pc ON p.id = pc.pipeline_id
            LEFT JOIN pipeline_stages ps ON p.id = ps.pipeline_id
            GROUP BY p.id, p.name, p.pipeline_type, o.name
            ORDER BY p.id;
        """)
        pipelines = cursor.fetchall()
        
        for pipeline in pipelines:
            pid, name, ptype, office, contacts, stages = pipeline
            print(f"\nPipeline: {name} (ID: {pid})")
            print(f"  Type: {ptype}")
            print(f"  Office: {office}")
            print(f"  Contacts: {contacts}")
            print(f"  Stages: {stages}")
            
            # Get stage details for this pipeline
            cursor.execute("""
                SELECT ps.name, COUNT(pc.contact_id)
                FROM pipeline_stages ps
                LEFT JOIN pipeline_contacts pc ON ps.id = pc.current_stage_id
                WHERE ps.pipeline_id = ?
                GROUP BY ps.id, ps.name
                ORDER BY ps."order";
            """, (pid,))
            stages = cursor.fetchall()
            
            print("  Stage breakdown:")
            for stage_name, stage_count in stages:
                print(f"    - {stage_name}: {stage_count} contacts")
        
        # Sample some pipeline contacts
        if pipeline_contacts_count > 0:
            print("\n=== Sample Pipeline Contacts ===")
            cursor.execute("""
                SELECT 
                    pc.id,
                    c.first_name || ' ' || c.last_name as contact_name,
                    p.name as pipeline_name,
                    ps.name as stage_name,
                    pc.entered_at,
                    pc.last_updated
                FROM pipeline_contacts pc
                JOIN contacts c ON pc.contact_id = c.id
                JOIN pipelines p ON pc.pipeline_id = p.id
                JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
                LIMIT 5;
            """)
            samples = cursor.fetchall()
            for sample in samples:
                print(f"\nContact Entry {sample[0]}:")
                print(f"  Contact: {sample[1]}")
                print(f"  Pipeline: {sample[2]}")
                print(f"  Stage: {sample[3]}")
                print(f"  Entered: {sample[4]}")
                print(f"  Last Updated: {sample[5]}")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_counts()