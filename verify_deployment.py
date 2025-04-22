#!/usr/bin/env python3
"""
Deployment verification script for Mobilize CRM
This script verifies the proper configuration for deployment.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables from files if they exist
for env_file in ['.env', '.env.production']:
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")

def check_env_variables():
    """Check critical environment variables"""
    print("\n=== Checking Environment Variables ===")
    
    critical_vars = [
        # Firebase Configuration
        'FIREBASE_PROJECT_ID',
        'FIREBASE_PRIVATE_KEY_ID',
        'FIREBASE_CLIENT_EMAIL',
        
        # Database Configuration
        'DATABASE_URL',
        
        # Application Configuration
        'SECRET_KEY',
        'FLASK_APP',
        'FLASK_ENV'
    ]
    
    missing = []
    for var in critical_vars:
        if os.environ.get(var):
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is NOT set")
            missing.append(var)
    
    if missing:
        print(f"\n⚠️ Missing {len(missing)} critical environment variables: {', '.join(missing)}")
    else:
        print("\n✅ All critical environment variables are set")
    
    return len(missing) == 0

def check_firebase_config():
    """Check Firebase configuration"""
    print("\n=== Checking Firebase Configuration ===")
    
    project_id = os.environ.get('FIREBASE_PROJECT_ID')
    if not project_id:
        print("❌ FIREBASE_PROJECT_ID is not set")
        return False
    
    # Check if we have all the necessary Firebase keys
    firebase_keys = [
        'FIREBASE_PRIVATE_KEY_ID',
        'FIREBASE_PRIVATE_KEY',
        'FIREBASE_CLIENT_EMAIL',
        'FIREBASE_CLIENT_ID',
        'FIREBASE_CLIENT_CERT_URL'
    ]
    
    missing_keys = [key for key in firebase_keys if not os.environ.get(key)]
    if missing_keys:
        print(f"❌ Missing Firebase keys: {', '.join(missing_keys)}")
        return False
    
    print("✅ Firebase configuration appears to be complete")
    return True

def check_database_connection():
    """Check database connection"""
    print("\n=== Checking Database Connection ===")
    
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL is not set")
        return False
    
    # Simple check to identify database type
    db_type = "unknown"
    if 'postgresql' in db_url:
        db_type = "PostgreSQL"
    elif 'mysql' in db_url:
        db_type = "MySQL"
    elif 'sqlite' in db_url:
        db_type = "SQLite"
    
    print(f"📊 Database type: {db_type}")
    print(f"✅ Database URL is set to {db_url[:15]}...")
    
    # Note: We could add actual connection testing here if needed
    return True

def main():
    """Main verification function"""
    print("=== Mobilize CRM Deployment Verification ===")
    print(f"Running verification at: {os.getcwd()}")
    
    # Run checks
    env_status = check_env_variables()
    firebase_status = check_firebase_config()
    db_status = check_database_connection()
    
    # Summarize results
    print("\n=== Verification Summary ===")
    print(f"Environment Variables: {'✅' if env_status else '❌'}")
    print(f"Firebase Configuration: {'✅' if firebase_status else '❌'}")
    print(f"Database Configuration: {'✅' if db_status else '❌'}")
    
    if env_status and firebase_status and db_status:
        print("\n✅ All checks passed! Deployment should succeed.")
        return 0
    else:
        print("\n⚠️ Some checks failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 