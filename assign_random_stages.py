import sqlite3
import random
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('instance/mobilize_crm.db')
cursor = conn.cursor()

# Get pipeline information
pipeline_id = 1  # Main Office People Pipeline
cursor.execute("SELECT id FROM pipeline_stages WHERE pipeline_id = ?", (pipeline_id,))
stages = [row[0] for row in cursor.fetchall()]

if not stages:
    print("No pipeline stages found for the main people pipeline. Exiting.")
    conn.close()
    exit(1)

# Get all people
cursor.execute("SELECT id FROM people")
people = [row[0] for row in cursor.fetchall()]

print(f"Found {len(people)} people and {len(stages)} pipeline stages")

# Current timestamp for the updates
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# First clean up any existing pipeline_contacts entries
print("Cleaning up existing pipeline contacts...")
cursor.execute("DELETE FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
print(f"Deleted {cursor.rowcount} existing pipeline contact entries.")

# Prepare for batch insertion
pipeline_entries = []
pipeline_stage_updates = []

for person_id in people:
    # Select a random stage for this person
    stage_id = random.choice(stages)
    
    # Get the stage name for the direct update to people table
    cursor.execute("SELECT name FROM pipeline_stages WHERE id = ?", (stage_id,))
    stage_name = cursor.fetchone()[0]
    
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
print(f"Updated {len(pipeline_stage_updates)} people")

# Commit the changes
print("Committing changes...")
conn.commit()
print("Changes committed.")

# Print summary
print(f"Successfully assigned random pipeline stages to {len(people)} people")
print("Distribution:")

# Show distribution of stages
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

# Verify the pipeline_contacts table has entries
cursor.execute("SELECT COUNT(*) FROM pipeline_contacts WHERE pipeline_id = ?", (pipeline_id,))
count = cursor.fetchone()[0]
print(f"Final verification: pipeline_contacts has {count} entries for pipeline_id {pipeline_id}")

# Close the connection
conn.close()
print("Database connection closed.") 