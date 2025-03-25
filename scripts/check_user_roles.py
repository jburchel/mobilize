#!/usr/bin/env python3
"""
Script to check user roles and permissions.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.user import User
from app.models.permission import Permission
from app.models.office import Office

def check_user_roles():
    """Check all users and their roles/permissions."""
    print("Checking user roles and permissions...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Get all users
            users = User.query.all()
            print(f"Found {len(users)} users")
            
            # Check each user
            for user in users:
                print(f"\nUser ID: {user.id}, Name: {user.first_name} {user.last_name}, Email: {user.email}")
                print(f"  Is active: {user.is_active}")
                
                if hasattr(user, 'created_at'):
                    print(f"  Created at: {user.created_at}")
                
                # Check user offices through user_offices relationship
                user_offices = []
                if hasattr(user, 'user_offices'):
                    user_offices = user.user_offices
                    office_names = []
                    for uo in user_offices:
                        office = Office.query.get(uo.office_id)
                        if office:
                            office_names.append(office.name)
                    print(f"  Offices: {office_names}")
                else:
                    print("  No offices attribute found")
                
                # Check permissions
                permissions = Permission.query.filter_by(user_id=user.id).all()
                permission_types = [p.permission_type for p in permissions]
                print(f"  Permissions: {permission_types}")
                
                # Check if Super Admin
                is_super_admin = 'super_admin' in permission_types
                print(f"  Is Super Admin: {is_super_admin}")
                
                # Check if Office Admin for any office
                office_admin_permissions = [p for p in permissions if p.permission_type == 'office_admin']
                if office_admin_permissions:
                    office_admin_for = []
                    for p in office_admin_permissions:
                        if p.office_id:
                            office = Office.query.get(p.office_id)
                            if office:
                                office_admin_for.append(office.name)
                    
                    if office_admin_for:
                        print(f"  Office Admin for: {office_admin_for}")
                    else:
                        print("  Office Admin but no specific offices")
                else:
                    print("  Not an Office Admin")
            
            # Specifically check if user "test" exists and is Super Admin
            test_user = User.query.filter_by(email='test@example.com').first()
            if test_user:
                test_permissions = Permission.query.filter_by(user_id=test_user.id).all()
                permission_types = [p.permission_type for p in test_permissions]
                is_super_admin = 'super_admin' in permission_types
                print(f"\nUser 'test@example.com' exists with ID {test_user.id}")
                print(f"Is Super Admin: {is_super_admin}")
                print(f"Permissions: {permission_types}")
            else:
                print("\nUser 'test@example.com' not found")
                
                # Check if any user has "test" in their username or email
                potential_test_users = User.query.filter(
                    (User.email.like('%test%')) | 
                    (User.first_name.like('%test%')) | 
                    (User.last_name.like('%test%'))
                ).all()
                
                if potential_test_users:
                    print("Found users with 'test' in their name or email:")
                    for user in potential_test_users:
                        permissions = Permission.query.filter_by(user_id=user.id).all()
                        permission_types = [p.permission_type for p in permissions]
                        is_super_admin = 'super_admin' in permission_types
                        print(f"  User ID: {user.id}, Name: {user.first_name} {user.last_name}, Email: {user.email}")
                        print(f"  Is Super Admin: {is_super_admin}")
                        print(f"  Permissions: {permission_types}")
    
    except Exception as e:
        print(f"\n❌ Error checking user roles: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    check_user_roles() 