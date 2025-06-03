#!/usr/bin/env python3
"""
Schema Migration Script for Mobilize CRM
This script handles running Flask DB migration commands to properly
initialize and apply migrations to the PostgreSQL database.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Ensure we're using the production database
os.environ['FLASK_ENV'] = 'production'

def run_command(cmd, description):
    """Run a shell command and print its output."""
    print(f"\n=== {description} ===")
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("Output:")
        print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Command failed with return code {result.returncode}")
        return False
    
    print(f"✅ {description} completed successfully")
    return True

def init_migrations():
    """Initialize the Flask DB migration environment."""
    return run_command(
        ["flask", "db", "init"],
        "Initializing migration environment"
    )

def generate_migration():
    """Generate a migration script for the current database state."""
    return run_command(
        ["flask", "db", "migrate", "-m", "initial_postgresql_migration"],
        "Generating migration script"
    )

def review_migration():
    """Review the generated migration script."""
    print("\n=== Reviewing migration script ===")
    
    # Find the most recent migration file
    migrations_dir = Path("migrations/versions")
    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        return False
    
    migration_files = list(migrations_dir.glob("*.py"))
    if not migration_files:
        print("❌ No migration files found")
        return False
    
    # Sort by modification time to get the most recent
    migration_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_migration = migration_files[0]
    
    print(f"Latest migration file: {latest_migration}")
    
    # Display the file content
    with open(latest_migration, 'r') as f:
        content = f.read()
        print("\nMigration content:")
        print("-" * 80)
        print(content)
        print("-" * 80)
    
    return True

def apply_migration():
    """Apply the migration to the PostgreSQL database."""
    return run_command(
        ["flask", "db", "upgrade"],
        "Applying migration"
    )

def verify_migration():
    """Verify that the migration was applied correctly."""
    print("\n=== Verifying migration ===")
    
    # Run verify_deployment.py script to check connection and alembic_version
    result = subprocess.run(
        ["python3", "scripts/deployment/verify_deployment.py"],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    if result.returncode != 0:
        print("❌ Migration verification failed")
        return False
    
    print("✅ Migration verification successful")
    return True

def main():
    print("=== Schema Migration for PostgreSQL ===")
    
    steps = [
        ("Initialize migration environment", init_migrations),
        ("Generate migration script", generate_migration),
        ("Review migration script", review_migration),
        ("Apply migration", apply_migration),
        ("Verify migration", verify_migration)
    ]
    
    for i, (description, step_func) in enumerate(steps):
        print(f"\nStep {i+1}/{len(steps)}: {description}")
        
        success = step_func()
        if not success:
            print(f"❌ Step {i+1} ({description}) failed. Migration process stopped.")
            return 1
        
        print(f"✅ Step {i+1} completed successfully")
        
        # Pause between steps
        if i < len(steps) - 1:
            print("\nPausing for 2 seconds before next step...")
            time.sleep(2)
    
    print("\n✅ All schema migration steps completed successfully!")
    print("You can now mark the 'Schema Migration' section as completed in the deployment checklist.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 