#!/usr/bin/env python3
"""
Application Configuration Verification Script
This script verifies that the application is properly configured to use
the PostgreSQL database and tests the database connection.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Set environment to production for testing
os.environ['FLASK_ENV'] = 'production'

# Root directory
ROOT_DIR = Path(__file__).parent.parent.parent.absolute()

def verify_env_files():
    """Verify that the environment files exist and contain the necessary settings."""
    env_prod_file = ROOT_DIR / '.env.production'
    
    if not env_prod_file.exists():
        print(f"❌ {env_prod_file} does not exist")
        return False
    
    print(f"✅ {env_prod_file} exists")
    
    # Check for required settings
    required_settings = ['DB_CONNECTION_STRING', 'FLASK_ENV']
    missing_settings = []
    
    with open(env_prod_file, 'r') as f:
        content = f.read()
        
        for setting in required_settings:
            if f"{setting}=" not in content:
                missing_settings.append(setting)
    
    if missing_settings:
        print(f"❌ Missing required settings in {env_prod_file}: {', '.join(missing_settings)}")
        return False
    
    print(f"✅ All required settings found in {env_prod_file}")
    return True

def verify_app_config():
    """Verify the application configuration."""
    try:
        # Import the app's config module
        sys.path.insert(0, str(ROOT_DIR))
        
        from app.config import config
        
        # Get the production config
        prod_config = config.get('production')
        
        if not prod_config:
            print("❌ Production configuration not found")
            return False
        
        # Instantiate the config class
        prod_config_instance = prod_config()
        
        # Check database URI
        db_uri = prod_config_instance.SQLALCHEMY_DATABASE_URI
        
        if not db_uri:
            print("❌ SQLALCHEMY_DATABASE_URI not set in production configuration")
            return False
        
        if not db_uri.startswith('postgresql://'):
            print(f"❌ SQLALCHEMY_DATABASE_URI is not a PostgreSQL URI: {db_uri}")
            return False
        
        print(f"✅ SQLALCHEMY_DATABASE_URI is set to a PostgreSQL URI")
        print(f"   {db_uri}")
        
        return True
    except Exception as e:
        print(f"❌ Error verifying app configuration: {e}")
        return False

def test_db_connection():
    """Test the database connection."""
    try:
        # Import Flask-SQLAlchemy
        sys.path.insert(0, str(ROOT_DIR))
        
        # Initialize the Flask app with production config
        from app import create_app
        app = create_app('production')
        
        # Get the database instance
        from app import db
        
        with app.app_context():
            # Test connection by executing a simple query
            result = db.session.execute("SELECT 1").scalar()
            
            if result != 1:
                print("❌ Database connection test failed")
                return False
            
            # Test database version
            version = db.session.execute("SELECT version()").scalar()
            print(f"✅ Successfully connected to the database")
            print(f"   PostgreSQL version: {version}")
            
            # Test a simple query on a table
            try:
                user_count = db.session.execute("SELECT COUNT(*) FROM users").scalar()
                print(f"✅ Found {user_count} users in the database")
            except Exception as e:
                print(f"❌ Failed to query users table: {e}")
            
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("=== Application Configuration Verification ===")
    
    # Verify environment files
    print("\n--- Environment Files ---")
    env_ok = verify_env_files()
    
    # Verify app configuration
    print("\n--- Application Configuration ---")
    app_config_ok = verify_app_config()
    
    # Test database connection
    print("\n--- Database Connection ---")
    db_ok = test_db_connection()
    
    # Overall status
    print("\n=== Verification Summary ===")
    print(f"Environment Files: {'✅ Pass' if env_ok else '❌ Fail'}")
    print(f"Application Configuration: {'✅ Pass' if app_config_ok else '❌ Fail'}")
    print(f"Database Connection: {'✅ Pass' if db_ok else '❌ Fail'}")
    
    if env_ok and app_config_ok and db_ok:
        print("\n✅ Application is properly configured to use PostgreSQL!")
        return 0
    else:
        print("\n❌ Application configuration has issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 