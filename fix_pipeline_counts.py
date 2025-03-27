import sqlite3
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('instance/mobilize_crm.db')
cursor = conn.cursor()

print("Diagnosing pipeline contact count issue...")

# Check for people pipeline
cursor.execute("SELECT id, name FROM pipelines WHERE is_main_pipeline = 1 AND pipeline_type = 'people'")
people_pipelines = cursor.fetchall()
print(f"Found {len(people_pipelines)} main people pipelines:")
for pipeline in people_pipelines:
    print(f"  Pipeline ID: {pipeline[0]}, Name: {pipeline[1]}")

# Check the current counts in pipeline_contacts
for pipeline_id, name in people_pipelines:
    cursor.execute("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
    count = cursor.fetchone()[0]
    print(f"  Pipeline ID: {pipeline_id}, Name: {name} has {count} contacts in pipeline_contacts table")
    
    # Check the contact_id values to make sure they're linked to people
    cursor.execute("""
        SELECT c.id, c.type 
        FROM contacts c 
        JOIN pipeline_contacts pc ON c.id = pc.contact_id 
        WHERE pc.pipeline_id = ? 
        GROUP BY c.type
    """, (pipeline_id,))
    types = cursor.fetchall()
    print(f"  Contact types in pipeline {pipeline_id}:")
    for contact_id, contact_type in types:
        cursor.execute("SELECT COUNT(*) FROM contacts c JOIN pipeline_contacts pc ON c.id = pc.contact_id WHERE pc.pipeline_id = ? AND c.type = ?", (pipeline_id, contact_type))
        type_count = cursor.fetchone()[0]
        print(f"    Type: {contact_type}, Count: {type_count}")

# The issue could be that the pipeline_type in the model is 'people' but contact type is 'person'
# Let's check both the pipeline model and the contact model implementations

# For the People Pipeline card to show 0 contacts while we have 57 in the database
# the most likely issue is that the pipeline's count_contacts() method is not finding the contacts
# even though they are in the database.

# Let's also check a potential type mismatch
cursor.execute("SELECT DISTINCT type FROM contacts")
contact_types = cursor.fetchall()
print("\nContact types in the system:")
for t in contact_types:
    print(f"  {t[0]}")

cursor.execute("SELECT DISTINCT pipeline_type FROM pipelines")
pipeline_types = cursor.fetchall()
print("\nPipeline types in the system:")
for t in pipeline_types:
    print(f"  {t[0]}")

# Let's see the ORM model definitions

print("\nChecking if there might be a filter in the PipelineContact relationship...")
cursor.execute("SELECT sql FROM sqlite_master WHERE name = 'pipelines'")
pipelines_schema = cursor.fetchone()[0]
print(f"Pipelines table schema: {pipelines_schema}")

# Close the connection
conn.close()

print("\nDiagnosis complete. Check the output for potential issues with pipeline contact counts.") 