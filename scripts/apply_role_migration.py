#!/usr/bin/env python3
"""
Script to apply role migrations and update role_id for existing users.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.user import User
from app.models.role import Role
from sqlalchemy import text

def apply_role_migration():
    """Apply the role migration and update existing users."""
    print("Applying role migration and updating users...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            print("Checking if roles table exists...")
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='roles'"))
            if not list(result):
                print("Roles table does not exist. Please run database migrations first.")
                return
            
            print("Checking for existing roles...")
            roles = Role.query.all()
            if not roles:
                print("No roles found. Please run database migrations first.")
                return
            
            # Create a mapping of role names to role ids
            role_mapping = {role.name: role.id for role in roles}
            print(f"Found roles: {role_mapping}")
            
            # Get all users
            users = User.query.all()
            print(f"Found {len(users)} users to update")
            
            # Update role_id based on existing role string
            updated_count = 0
            for user in users:
                if user.role in role_mapping:
                    user.role_id = role_mapping[user.role]
                    updated_count += 1
                elif user.role == 'admin':  # Special case for 'admin'
                    user.role_id = role_mapping['office_admin']
                    user.role = 'office_admin'  # Update the role string too
                    updated_count += 1
                else:
                    # Default to standard_user if role not recognized
                    user.role_id = role_mapping['standard_user']
                    user.role = 'standard_user'
                    updated_count += 1
            
            db.session.commit()
            print(f"Successfully updated {updated_count} users with role_id values")
            
    except Exception as e:
        print(f"Error applying role migration: {str(e)}")
        raise

if __name__ == "__main__":
    apply_role_migration()
    print("Role migration complete!") 