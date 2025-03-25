#!/usr/bin/env python3
"""
Script to check the permission table schema.
"""

import os
import sys
from pathlib import Path
import sqlite3

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app

def check_permissions_schema():
    """Check permissions table schema and data."""
    print("Checking permissions table schema and data...")
    
    try:
        # Create app to get the database URI
        app = create_app()
        
        # Get the database path from the URI
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_path = db_uri.replace('sqlite:///', '')
        
        if not os.path.isabs(db_path):
            db_path = os.path.join(project_root, db_path)
        
        print(f"Database path: {db_path}")
        
        # Connect to the database directly
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Use row factory for named columns
        cursor = conn.cursor()
        
        # Check all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Check permissions table schema
        if 'permissions' in tables:
            print("\n=== Permissions Table Schema ===")
            cursor.execute("PRAGMA table_info(permissions);")
            columns = cursor.fetchall()
            for col in columns:
                print(f"Column: {col['name']} ({col['type']})")
            
            # Check permissions table data
            print("\n=== Permissions Table Data ===")
            cursor.execute("SELECT * FROM permissions;")
            permissions = cursor.fetchall()
            print(f"Found {len(permissions)} permission records")
            
            for p in permissions:
                print("\nPermission:")
                for col in columns:
                    col_name = col['name']
                    print(f"  {col_name}: {p[col_name]}")
        
        # Check for user permissions junction table
        for table_name in ['user_permissions', 'user_roles']:
            if table_name in tables:
                print(f"\n=== {table_name} Table Schema ===")
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"Column: {col['name']} ({col['type']})")
                
                print(f"\n=== {table_name} Table Data ===")
                cursor.execute(f"SELECT * FROM {table_name};")
                data = cursor.fetchall()
                print(f"Found {len(data)} records")
                
                for row in data:
                    print("\nRecord:")
                    for col in columns:
                        col_name = col['name']
                        print(f"  {col_name}: {row[col_name]}")
        
        # Check user-office table
        print("\n=== User-Office Relationships ===")
        if 'user_offices' in tables:
            cursor.execute("PRAGMA table_info(user_offices);")
            columns = cursor.fetchall()
            for col in columns:
                print(f"Column: {col['name']} ({col['type']})")
            
            cursor.execute("SELECT * FROM user_offices;")
            user_offices = cursor.fetchall()
            print(f"\nFound {len(user_offices)} user-office relationships")
            
            # Get user and office information for each relationship
            for uo in user_offices:
                user_id = uo['user_id']
                office_id = uo['office_id']
                
                cursor.execute("SELECT first_name, last_name, email FROM users WHERE id = ?;", (user_id,))
                user = cursor.fetchone()
                
                cursor.execute("SELECT name FROM offices WHERE id = ?;", (office_id,))
                office = cursor.fetchone()
                
                if user and office:
                    print(f"User {user['first_name']} {user['last_name']} ({user['email']}) is in office {office['name']}")
        
        # Close the connection
        conn.close()
    
    except Exception as e:
        print(f"\n❌ Error checking permissions schema: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    check_permissions_schema() 