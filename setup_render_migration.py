#!/usr/bin/env python3
"""
Setup Script for Render to Supabase Migration

This script helps set up the environment for migrating data from 
Render PostgreSQL to Supabase PostgreSQL by updating environment files
and creating necessary configuration.

Usage:
    python setup_render_migration.py

This will:
1. Prompt for Render PostgreSQL connection string
2. Update .env.production with the RENDER_DB_URL variable
3. Create a mapping configuration template if needed
"""

import os
import sys
import re
from getpass import getpass
from dotenv import load_dotenv

def check_env_files():
    """Check if necessary environment files exist"""
    if not os.path.exists('.env.production'):
        print("Creating .env.production file...")
        with open('.env.production', 'w') as f:
            f.write("# Production Environment Variables\n\n")
            f.write("# Supabase PostgreSQL URL\n")
            f.write("DATABASE_URL=\n\n")
            f.write("# Render PostgreSQL URL (for migration)\n")
            f.write("RENDER_DB_URL=\n")
    else:
        print("Found existing .env.production file")

def is_valid_pg_url(url):
    """Validate PostgreSQL connection URL format"""
    # Very basic validation - just check if it starts with postgres(ql)://
    return url.startswith('postgres://') or url.startswith('postgresql://')

def update_env_file(render_url):
    """Update .env.production with Render DB URL"""
    # Load existing environment
    load_dotenv('.env.production')
    
    # Check if DATABASE_URL is set
    supabase_url = os.getenv('DATABASE_URL')
    if not supabase_url:
        print("\nWARNING: DATABASE_URL not set in .env.production")
        supabase_url = input("Enter Supabase PostgreSQL URL: ")
        if not is_valid_pg_url(supabase_url):
            print("Invalid PostgreSQL URL format. Please check and try again.")
            sys.exit(1)
    
    # Read current file content
    with open('.env.production', 'r') as f:
        content = f.read()
    
    # Update RENDER_DB_URL
    if 'RENDER_DB_URL=' in content:
        content = re.sub(r'RENDER_DB_URL=.*', f'RENDER_DB_URL={render_url}', content)
    else:
        content += f"\n# Render PostgreSQL URL (for migration)\nRENDER_DB_URL={render_url}\n"
    
    # Update DATABASE_URL if needed
    if 'DATABASE_URL=' in content and not os.getenv('DATABASE_URL'):
        content = re.sub(r'DATABASE_URL=.*', f'DATABASE_URL={supabase_url}', content)
    
    # Write updated content
    with open('.env.production', 'w') as f:
        f.write(content)
    
    print("Updated .env.production with database URLs")

def check_migration_dependencies():
    """Check for required Python packages"""
    try:
        import psycopg2
        import dotenv
        print("Required packages installed (psycopg2, python-dotenv)")
    except ImportError:
        print("\nMissing required packages. Install with:")
        print("pip install psycopg2-binary python-dotenv")
        sys.exit(1)

def create_table_map_template():
    """Create a template file for table and column mappings"""
    if os.path.exists('migration_mappings.py'):
        print("Found existing migration_mappings.py file")
        return
    
    print("Creating migration_mappings.py template...")
    
    with open('migration_mappings.py', 'w') as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Table and Column Mappings for Render to Supabase Migration

This file contains mapping configurations to handle schema differences
between Render and Supabase databases during migration.
\"\"\"

# Tables to migrate (in order)
TABLES_IN_ORDER = [
    'users',
    'offices',
    'pipelines',
    'pipeline_stages',
    'people',
    'contacts',
    'pipeline_contacts',
    'pipeline_stage_history',
    'tasks',
    'notes',
    'churches',
    'communications',
    'phone_numbers',
    'addresses',
    'google_tokens',
    'email_templates',
    'email_signatures',
    'email_campaigns',
    'email_tracking',
    # Add other tables as needed
]

# Tables to completely skip during migration
SKIP_TABLES = [
    'alembic_version',
    # Add other tables to skip
]

# Column mappings for tables where schema has changed
# Format: {'table_name': {'old_column': 'new_column'}}
COLUMN_MAPPINGS = {
    # Example: If 'user' table in Render has 'name' but Supabase has 'full_name'
    # 'users': {'name': 'full_name'}
}

# Tables and columns to exclude from migration
EXCLUDE_COLUMNS = {
    # Example: 'users': ['deprecated_field1', 'deprecated_field2']
}

# Custom transformations for specific columns
# Format: {'table_name': {'column_name': lambda value: transformed_value}}
COLUMN_TRANSFORMATIONS = {
    # Example: 'users': {'is_active': lambda v: True if v == 1 else False}
}
""")
    
    print("Created migration_mappings.py template")

def main():
    print("Setting up Render to Supabase Migration")
    print("======================================\n")
    
    # Check dependencies
    check_migration_dependencies()
    
    # Check environment files
    check_env_files()
    
    # Get Render PostgreSQL URL
    print("\nEnter Render PostgreSQL connection details:")
    render_url = input("Render PostgreSQL URL (postgres://username:password@host:port/database): ")
    
    # Validate URL format
    if not is_valid_pg_url(render_url):
        print("Invalid PostgreSQL URL format. Please check and try again.")
        sys.exit(1)
    
    # Update environment file
    update_env_file(render_url)
    
    # Create mapping template
    create_table_map_template()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Run schema comparison: python schema_comparison.py")
    print("2. Review schema_diff_report.txt and update migration_mappings.py as needed")
    print("3. Run migration with dry-run first: python migrate_render_to_supabase.py --dry-run")
    print("4. When ready, run actual migration: python migrate_render_to_supabase.py")

if __name__ == "__main__":
    main() 