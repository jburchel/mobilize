#!/usr/bin/env python3
"""
Table and Column Mappings for Render to Supabase Migration

This file contains mapping configurations to handle schema differences
between Render and Supabase databases during migration.
"""

# Tables to migrate (in order)
TABLES_IN_ORDER = [
    'userprofile_customuser',     # Django users to migrate to 'users'
    'contacts_people',            # Maps to 'people'
    'contacts_church',            # Maps to 'churches'
    'contacts_contact',           # Maps to 'contacts'
    'task_tracker_task',          # Maps to 'tasks'
    'com_log_comlog',             # Maps to 'communications'
]

# Tables to completely skip during migration
SKIP_TABLES = [
    'auth_group',
    'auth_group_permissions',
    'auth_permission',
    'django_admin_log',
    'django_content_type',
    'django_migrations',
    'django_session',
    'userprofile_customuser_groups',
    'userprofile_customuser_user_permissions',
    'alembic_version',
]

# Table name mappings
TABLE_MAPPINGS = {
    'userprofile_customuser': 'users',
    'contacts_people': 'people',
    'contacts_church': 'churches',
    'contacts_contact': 'contacts',
    'task_tracker_task': 'tasks', 
    'com_log_comlog': 'communications',
}

# Column mappings for tables where schema has changed
# Format: {'table_name': {'old_column': 'new_column'}}
COLUMN_MAPPINGS = {
    'userprofile_customuser': {
        'id': 'id',
        'password': 'firebase_uid',        # Map password hash to firebase_uid
        'last_login': 'last_login',
        'is_superuser': 'role',            # Transform below
        'email': 'email',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'date_joined': 'created_at',
        'is_active': 'is_active',
    },
    'contacts_people': {
        'id': 'id',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'email': 'email',
        'phone': 'phone',
        'address': 'address_street',
        'city': 'address_city',
        'state': 'address_state',
        'zip_code': 'address_zip',
        'created_date': 'created_at',
        'modified_date': 'updated_at',
    },
    'contacts_church': {
        'id': 'id',
        'name': 'name',
        'email': 'email',
        'phone': 'phone',
        'address': 'address_street',
        'city': 'address_city',
        'state': 'address_state',
        'zip_code': 'address_zip',
        'created_date': 'created_at',
        'modified_date': 'updated_at',
    },
    'task_tracker_task': {
        'id': 'id',
        'title': 'title',
        'description': 'description',
        'due_date': 'due_date',
        'completed': 'status',        # Transform below
        'assigned_to_id': 'assigned_to', 
        'created_date': 'created_at',
        'modified_date': 'updated_at',
    },
    'com_log_comlog': {
        'id': 'id',
        'subject': 'subject',
        'message': 'content',
        'communication_date': 'date',
        'communication_type': 'type',
        'created_date': 'created_at',
        'modified_date': 'updated_at',
    }
}

# Tables and columns to exclude from migration
EXCLUDE_COLUMNS = {
    # Columns to exclude for each table
    'userprofile_customuser': ['is_staff', 'username'],
    'contacts_people': ['notes'],
    'contacts_church': ['notes'],
    'task_tracker_task': ['priority'],
}

# Custom transformations for specific columns
# Format: {'table_name': {'column_name': lambda value: transformed_value}}
COLUMN_TRANSFORMATIONS = {
    'userprofile_customuser': {
        'role': lambda v: 'admin' if v else 'standard_user',
    },
    'task_tracker_task': {
        'status': lambda v: 'completed' if v else 'pending',
    },
}

# Special SQL transformations - these are executed directly instead of row-by-row
# Format: {'supabase_table': 'SQL statement with {render_table} placeholder'}
CUSTOM_SQL_TRANSFORMS = {
    # Example of complex transformations using SQL
    # 'contacts': '''
    #     INSERT INTO contacts (id, type, email, phone, address_street, user_id, created_at, updated_at)
    #     SELECT id, 'person', email, phone, address, created_by_id, created_date, modified_date 
    #     FROM {render_table} WHERE type = 'person'
    # ''',
}
