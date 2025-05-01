#!/usr/bin/env python3
"""
Ensure Migrations Script for Mobilize CRM
This script makes sure all migrations are applied to the PostgreSQL database.
"""

import os
import sys
import subprocess
import time

# Set environment to production
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_APP'] = 'app.py'

def run_upgrade():
    """Run the Flask DB upgrade command"""
    print("Running Flask DB upgrade to apply all migrations...")
    
    # Run the Flask DB upgrade command
    result = subprocess.run(
        ["python3", "-m", "flask", "db", "upgrade"],
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print("Output:")
        print(result.stdout)
    
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    print("Upgrade completed")
    
    # Verify the upgrade by checking current version
    check_result = subprocess.run(
        ["python3", "scripts/deployment/check_alembic.py"],
        capture_output=True,
        text=True
    )
    
    if check_result.stdout:
        print(check_result.stdout)
    
    if check_result.stderr:
        print("Verification Errors:")
        print(check_result.stderr)

def main():
    print("=== Ensuring Migrations are Applied ===")
    
    # Run Flask DB upgrade
    run_upgrade()
    
    print("Now running comprehensive verification...")
    time.sleep(1)
    
    # Run the comprehensive verification script
    verify_result = subprocess.run(
        ["python3", "scripts/deployment/verify_migration.py"],
        capture_output=False,  # Show output directly
        text=True
    )
    
    if verify_result.returncode != 0:
        print("❌ Verification failed after applying migrations.")
        return 1
    
    print("\n✅ Migrations have been successfully applied and verified!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 