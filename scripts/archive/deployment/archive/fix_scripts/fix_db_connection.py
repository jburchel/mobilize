#!/usr/bin/env python3

"""
Script to check and fix the database connection in the Cloud Run environment.

This script addresses the error: 
'The current Flask app is not registered with this SQLAlchemy instance.'

Usage:
    python3 fix_db_connection.py
"""

import os
import sys

# Check if we're running in Cloud Run
def is_cloud_run():
    return os.environ.get('K_SERVICE') is not None

# Main function
def main():
    # Print environment variables for debugging
    print("Environment variables:")
    print(f"FLASK_APP: {os.environ.get('FLASK_APP')}")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    print(f"DATABASE_URL: {'Set' if os.environ.get('DATABASE_URL') else 'Not set'}")
    print(f"DB_CONNECTION_STRING: {'Set' if os.environ.get('DB_CONNECTION_STRING') else 'Not set'}")
    print(f"SQLALCHEMY_DATABASE_URI: {'Set' if os.environ.get('SQLALCHEMY_DATABASE_URI') else 'Not set'}")
    print(f"Running in Cloud Run: {is_cloud_run()}")
    
    # Check if we're running in Cloud Run
    if is_cloud_run():
        # Check if DB_CONNECTION_STRING is set
        db_connection_string = os.environ.get('DB_CONNECTION_STRING')
        if not db_connection_string:
            print("Error: DB_CONNECTION_STRING environment variable not set in Cloud Run.")
            print("Please set it using:")
            print("gcloud run services update mobilize-crm --region us-central1 --update-env-vars DB_CONNECTION_STRING=your_postgresql_connection_string")
            sys.exit(1)
        
        # Check if DATABASE_URL is set
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("Warning: DATABASE_URL environment variable not set in Cloud Run.")
            print("Setting DATABASE_URL to the value of DB_CONNECTION_STRING...")
            os.environ['DATABASE_URL'] = db_connection_string
            print("DATABASE_URL set successfully.")
        
        # Check if SQLALCHEMY_DATABASE_URI is set
        sqlalchemy_uri = os.environ.get('SQLALCHEMY_DATABASE_URI')
        if not sqlalchemy_uri:
            print("Warning: SQLALCHEMY_DATABASE_URI environment variable not set in Cloud Run.")
            print("Setting SQLALCHEMY_DATABASE_URI to the value of DB_CONNECTION_STRING...")
            os.environ['SQLALCHEMY_DATABASE_URI'] = db_connection_string
            print("SQLALCHEMY_DATABASE_URI set successfully.")
    else:
        print("Not running in Cloud Run. No changes needed.")
    
    print("Database connection check completed.")

if __name__ == "__main__":
    main()
