#!/usr/bin/env python
"""
Script to add default permissions and role-permission mappings to the database.
"""
import os
import sys
from app import create_app
from app.extensions import db
from app.models import Role, Permission, RolePermission, User

def add_default_permissions():
    """Add default permissions and role-permission mappings"""
    app = create_app()
    
    with app.app_context():
        # Create default permissions if they don't exist
        permissions = {
            'view_dashboard': 'Can view dashboard and statistics',
            'manage_users': 'Can create, edit, and delete users',
            'manage_roles': 'Can create, edit, and delete roles and permissions',
            'view_users': 'Can view user profiles and information',
            'manage_churches': 'Can create, edit, and delete churches',
            'view_churches': 'Can view church information',
            'manage_people': 'Can create, edit, and delete people',
            'view_people': 'Can view people information',
            'manage_tasks': 'Can create, edit, and delete tasks',
            'view_tasks': 'Can view tasks',
            'manage_communications': 'Can create, edit, and delete communications',
            'view_communications': 'Can view communications',
            'manage_offices': 'Can create, edit, and delete offices',
            'view_offices': 'Can view office information',
            'manage_settings': 'Can modify system settings',
            'view_settings': 'Can view system settings',
            'manage_pipelines': 'Can create, edit, and delete pipelines',
            'view_pipelines': 'Can view pipelines',
            'sync_google': 'Can sync with Google services',
            'access_reports': 'Can access reporting features',
            'export_data': 'Can export data from the system',
            'import_data': 'Can import data into the system',
            'system_admin': 'Full system administration privileges',
        }
        
        created_permissions = {}
        for name, description in permissions.items():
            perm = Permission.query.filter_by(name=name).first()
            if not perm:
                perm = Permission(name=name, description=description)
                db.session.add(perm)
                print(f"Created permission: {name}")
            created_permissions[name] = perm
        
        # Get or create roles
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if not super_admin_role:
            super_admin_role = Role(name='super_admin', description='Full administrative access to all features')
            db.session.add(super_admin_role)
            print("Created role: super_admin")
        
        office_admin_role = Role.query.filter_by(name='office_admin').first()
        if not office_admin_role:
            office_admin_role = Role(name='office_admin', description='Administrative access limited to office scope')
            db.session.add(office_admin_role)
            print("Created role: office_admin")
        
        standard_user_role = Role.query.filter_by(name='standard_user').first()
        if not standard_user_role:
            standard_user_role = Role(name='standard_user', description='Regular user with basic access')
            db.session.add(standard_user_role)
            print("Created role: standard_user")
        
        # Define permission sets for each role
        role_permissions = {
            'super_admin': list(permissions.keys()),  # All permissions
            'office_admin': [
                'view_dashboard', 'view_users', 'manage_users',
                'manage_churches', 'view_churches',
                'manage_people', 'view_people',
                'manage_tasks', 'view_tasks',
                'manage_communications', 'view_communications',
                'view_offices',
                'view_settings',
                'manage_pipelines', 'view_pipelines',
                'sync_google',
                'access_reports',
                'export_data', 'import_data'
            ],
            'standard_user': [
                'view_dashboard',
                'view_users',
                'view_churches',
                'view_people',
                'manage_tasks', 'view_tasks',
                'manage_communications', 'view_communications',
                'view_pipelines',
                'sync_google',
            ]
        }
        
        # Assign permissions to roles
        for role_name, perm_names in role_permissions.items():
            role = Role.query.filter_by(name=role_name).first()
            if role:
                # Clear existing permissions
                RolePermission.query.filter_by(role_id=role.id).delete()
                
                # Add new permissions
                for perm_name in perm_names:
                    perm = created_permissions.get(perm_name)
                    if perm:
                        role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                        db.session.add(role_perm)
                        print(f"Assigned permission '{perm_name}' to role '{role_name}'")
        
        # Update user role_id values
        users = User.query.all()
        for user in users:
            if user.role and not user.role_id:
                role = Role.query.filter_by(name=user.role).first()
                if role:
                    user.role_id = role.id
                    print(f"Updated user {user.email} with role_id for {user.role}")
        
        # Commit all changes
        db.session.commit()
        print("Completed successfully!")

if __name__ == '__main__':
    add_default_permissions() 