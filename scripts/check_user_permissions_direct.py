#!/usr/bin/env python3
"""
Script to directly check user permissions in the database.
"""

import os
import sys
from pathlib import Path
import sqlite3

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app

def check_user_permissions_direct():
    """Check user permissions directly in the database."""
    print("Checking user permissions directly in the database...")
    
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
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables in database: {tables}")
        
        # Get all users
        cursor.execute("SELECT * FROM users;")
        users = cursor.fetchall()
        print(f"\nFound {len(users)} users:")
        
        # Print user information
        for user in users:
            user_id = user['id']
            print(f"\nUser ID: {user_id}")
            print(f"  Name: {user['first_name']} {user['last_name']}")
            print(f"  Email: {user['email']}")
            print(f"  Is active: {user['is_active']}")
            
            # Check user-office relationship
            cursor.execute("SELECT * FROM user_offices WHERE user_id = ?;", (user_id,))
            user_offices = cursor.fetchall()
            
            if user_offices:
                print(f"  Associated with {len(user_offices)} offices:")
                for uo in user_offices:
                    office_id = uo['office_id']
                    cursor.execute("SELECT name FROM offices WHERE id = ?;", (office_id,))
                    office_name = cursor.fetchone()
                    if office_name:
                        print(f"    Office ID: {office_id}, Name: {office_name[0]}")
            else:
                print("  Not associated with any offices")
            
            # Look for permissions tables
            if 'permissions' in tables:
                cursor.execute("SELECT * FROM permissions WHERE user_id = ?;", (user_id,))
                permissions = cursor.fetchall()
                if permissions:
                    print(f"  Found {len(permissions)} permissions:")
                    for p in permissions:
                        print(f"    Permission ID: {p['id']}, Type: {p.get('permission_type', 'N/A')}")
                else:
                    print("  No permissions found")
            
            # Try different permissions table formats
            for permissions_table in ['user_permissions', 'user_roles', 'roles']:
                if permissions_table in tables:
                    cursor.execute(f"SELECT * FROM {permissions_table} WHERE user_id = ?;", (user_id,))
                    permissions = cursor.fetchall()
                    if permissions:
                        print(f"  Found {len(permissions)} entries in {permissions_table}:")
                        for p in permissions:
                            column_names = [column[0] for column in cursor.description]
                            for col in column_names:
                                if col != 'user_id' and col != 'id':
                                    print(f"    {col}: {p[col]}")
        
        # Specifically look for Super Admin users
        print("\n=== Looking for Super Admin users ===")
        for table in ['permissions', 'user_permissions', 'user_roles', 'roles']:
            if table in tables:
                try:
                    # Try different field names for super admin
                    for field in ['permission_type', 'role_type', 'type', 'name']:
                        try:
                            cursor.execute(f"SELECT user_id FROM {table} WHERE {field} = 'super_admin';")
                            super_admins = cursor.fetchall()
                            if super_admins:
                                print(f"Found {len(super_admins)} super admins in {table} table with {field} field:")
                                for admin in super_admins:
                                    user_id = admin['user_id']
                                    cursor.execute("SELECT first_name, last_name, email FROM users WHERE id = ?;", (user_id,))
                                    user = cursor.fetchone()
                                    if user:
                                        print(f"  User ID: {user_id}, Name: {user['first_name']} {user['last_name']}, Email: {user['email']}")
                        except:
                            pass
                except:
                    pass
        
        # Check the schema of important tables
        print("\n=== Database Schema ===")
        for table in ['users', 'permissions', 'user_permissions', 'user_roles', 'user_offices']:
            if table in tables:
                cursor.execute(f"PRAGMA table_info({table});")
                columns = cursor.fetchall()
                print(f"\nTable: {table}")
                for col in columns:
                    print(f"  {col['name']} ({col['type']})")
        
        # Close the connection
        conn.close()
    
    except Exception as e:
        print(f"\n❌ Error checking user permissions: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    check_user_permissions_direct() 