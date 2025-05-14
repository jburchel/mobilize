#!/usr/bin/env python3
"""
Deployment Verification Script for Mobilize CRM
This script verifies that the application can connect to the PostgreSQL database
and checks various configuration settings.
"""

import os
import sys
from pathlib import Path

def verify_environment_files():
    """Check for the presence of environment files."""
    env_file = Path(".env")
    env_prod_file = Path(".env.production")
    
    print("Checking environment files...")
    
    if env_file.exists():
        print(f"✅ {env_file} exists")
        with open(env_file, 'r') as f:
            content = f.read()
            if "FLASK_ENV=production" in content:
                print("✅ FLASK_ENV is set to production")
            else:
                print("❌ FLASK_ENV is not set to production")
            
            if "DB_CONNECTION_STRING=" in content or "SQLALCHEMY_DATABASE_URI=" in content:
                print("✅ Database connection string is configured")
            else:
                print("❌ Database connection string is not configured")
    else:
        print(f"❌ {env_file} does not exist")
    
    if env_prod_file.exists():
        print(f"✅ {env_prod_file} exists")
    else:
        print(f"❌ {env_prod_file} does not exist")

def verify_database_connection():
    """Verify that the application can connect to the database."""
    try:
        print("\nVerifying database connection through the application...")
        
        # Import the application
        from app import create_app
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import text
        
        # Create the application instance
        app = create_app()
        
        # Print the database URL (masked password)
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        masked_url = db_url
        if '@' in db_url and ':' in db_url.split('@')[0]:
            parts = db_url.split('@')
            user_pass = parts[0].split(':')
            if len(user_pass) > 1:
                masked_url = f"{user_pass[0]}:******@{parts[1]}"
        
        print(f"Database URL (masked): {masked_url}")
        
        # Check if the database URL is a PostgreSQL URL
        if not db_url.startswith('postgresql://'):
            print("❌ Database URL is not a PostgreSQL URL")
            return False
        
        # Test the connection
        with app.app_context():
            result = app.extensions['sqlalchemy'].db.session.execute(text('SELECT 1'))
            if result.fetchone()[0] == 1:
                print("✅ Successfully connected to the database")
                return True
            else:
                print("❌ Failed to connect to the database")
                return False
            
    except Exception as e:
        print(f"❌ Error verifying database connection: {e}")
        return False

def verify_alembic_version():
    """Verify that the alembic_version table exists and has the correct version."""
    try:
        print("\nVerifying alembic_version table...")
        
        # Import the application
        from app import create_app
        from flask_sqlalchemy import SQLAlchemy
        from sqlalchemy import text
        
        # Create the application instance
        app = create_app()
        
        # Test the connection
        with app.app_context():
            result = app.extensions['sqlalchemy'].db.session.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'alembic_version')")
            )
            table_exists = result.fetchone()[0]
            
            if table_exists:
                print("✅ alembic_version table exists")
                
                result = app.extensions['sqlalchemy'].db.session.execute(
                    text("SELECT version_num FROM alembic_version")
                )
                version = result.fetchone()
                if version:
                    print(f"✅ Current version: {version[0]}")
                else:
                    print("❌ No version found in alembic_version table")
            else:
                print("❌ alembic_version table does not exist")
                
            return table_exists
            
    except Exception as e:
        print(f"❌ Error verifying alembic_version table: {e}")
        return False

def main():
    print("=== Deployment Verification ===")
    
    verify_environment_files()
    
    db_connection = verify_database_connection()
    if not db_connection:
        print("\n❌ Database connection verification failed!")
        return 1
    
    alembic_version = verify_alembic_version()
    if not alembic_version:
        print("\n❌ Alembic version verification failed!")
        return 1
    
    print("\n✅ All checks passed! The application is configured correctly for PostgreSQL.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 