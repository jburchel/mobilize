#!/usr/bin/env python3
import sqlite3
import random
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('instance/mobilize_crm.db')
cursor = conn.cursor()

# First, get information about the database structure
print("Checking database tables...")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Database has {len(tables)} tables:")
for table in tables:
    print(f"  - {table[0]}")

# Get People main pipeline ID - should be 1
pipeline_id = 1
cursor.execute("SELECT id, name, pipeline_type, is_main_pipeline FROM pipelines WHERE id = ?", (pipeline_id,))
pipeline = cursor.fetchone()
if not pipeline:
    print(f"Error: Pipeline with ID {pipeline_id} not found!")
    conn.close()
    exit(1)

print(f"Using pipeline: ID={pipeline[0]}, Name={pipeline[1]}, Type={pipeline[2]}, Main={pipeline[3]}")

# Get pipeline stages
cursor.execute("SELECT id, name FROM pipeline_stages WHERE pipeline_id = ?", (pipeline_id,))
stages = cursor.fetchall()
if not stages:
    print(f"Error: No stages found for pipeline {pipeline_id}!")
    conn.close()
    exit(1)

print(f"Found {len(stages)} stages:")
for stage in stages:
    print(f"  - ID: {stage[0]}, Name: {stage[1]}")

# Get people from the people table
cursor.execute("SELECT id, first_name, last_name FROM people")
people = cursor.fetchall()
print(f"Found {len(people)} people")

# Current timestamp for the updates
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Check if entries already exist in pipeline_contacts
cursor.execute("SELECT count(*) FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
existing_count = cursor.fetchone()[0]
print(f"Found {existing_count} existing pipeline contacts")

# Clean up existing entries
if existing_count > 0:
    print("Deleting existing pipeline_contacts entries...")
    cursor.execute("DELETE FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
    print(f"Deleted {cursor.rowcount} existing entries")

# Check if people exist in the contacts table
print("Checking if people are properly registered in the contacts table...")
for person in people:
    person_id = person[0]
    cursor.execute("SELECT id FROM contacts WHERE id = ?", (person_id,))
    contact = cursor.fetchone()
    if not contact:
        print(f"  ❌ Person ID {person_id} NOT found in contacts table. Adding...")
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, created_at) VALUES (?, ?, ?, ?)",
            (person_id, person[1], person[2], current_time)
        )
    else:
        print(f"  ✅ Person ID {person_id} found in contacts table")

# Prepare for batch insertion
pipeline_entries = []
pipeline_stage_updates = []

for person in people:
    person_id = person[0]
    
    # Select a random stage for this person
    stage = random.choice(stages)
    stage_id = stage[0]
    stage_name = stage[1]
    
    # Add to pipeline_contacts
    pipeline_entries.append((person_id, pipeline_id, stage_id, current_time, current_time))
    
    # Update people table pipeline_stage
    pipeline_stage_updates.append((stage_name, person_id))
    
    print(f"Prepared person_id: {person_id}, stage_id: {stage_id}, stage_name: {stage_name}")

# Insert into pipeline_contacts
print("Inserting into pipeline_contacts...")
cursor.executemany(
    "INSERT INTO pipeline_contacts (contact_id, pipeline_id, current_stage_id, entered_at, last_updated) VALUES (?, ?, ?, ?, ?)",
    pipeline_entries
)
print(f"Inserted {len(pipeline_entries)} entries into pipeline_contacts")

# Update people table
print("Updating people table...")
cursor.executemany(
    "UPDATE people SET pipeline_stage = ? WHERE id = ?",
    pipeline_stage_updates
)
print(f"Updated {len(pipeline_stage_updates)} people with pipeline stages")

# Commit the changes
print("Committing changes...")
conn.commit()
print("Changes committed.")

# Verify pipeline contacts count
cursor.execute("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
final_count = cursor.fetchone()[0]
print(f"Final verification: pipeline_contacts has {final_count} entries for pipeline_id {pipeline_id}")

# Show distribution of stages
print("Distribution:")
cursor.execute("""
    SELECT ps.name, COUNT(pc.contact_id) 
    FROM pipeline_contacts pc
    JOIN pipeline_stages ps ON pc.current_stage_id = ps.id
    WHERE pc.pipeline_id = ?
    GROUP BY ps.name
""", (pipeline_id,))

distribution = cursor.fetchall()
for stage_name, count in distribution:
    print(f"  {stage_name}: {count} people")

# Close the connection
conn.close()
print("Database connection closed.") 