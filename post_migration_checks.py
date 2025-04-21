#!/usr/bin/env python3
"""
Post-Migration Validation Script for Mobilize CRM

This script performs validation checks on the PostgreSQL database after
the data migration to ensure data integrity and consistency.

Usage:
    python post_migration_checks.py

Requirements:
    - psycopg2-binary
    - python-dotenv
"""

import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# PostgreSQL configuration
PG_CONNECTION = os.getenv('DATABASE_URL')

# Tables to check
TABLES = [
    'users',
    'offices',
    'people',
    'contacts',
    'churches',
    'pipelines',
    'pipeline_stages',
    'pipeline_contacts',
    'pipeline_stage_history',
    'tasks',
    'communications',
    'google_tokens',
    'permissions',
    'roles',
    'role_permissions',
    'user_roles',
    'email_templates',
    'email_signatures',
    'email_campaigns',
    'email_tracking'
]

def get_table_counts(cursor):
    """Get row counts for all tables"""
    counts = {}
    for table in TABLES:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            counts[table] = count
        except Exception as e:
            print(f"Error counting rows in {table}: {e}")
            counts[table] = "ERROR"
    return counts

def check_foreign_keys(cursor):
    """Check for foreign key violations"""
    violations = []
    
    # Common foreign key relationships to check
    relationships = [
        ('contacts', 'id', 'pipeline_contacts', 'contact_id'),
        ('pipeline_stages', 'id', 'pipeline_contacts', 'stage_id'),
        ('pipelines', 'id', 'pipeline_stages', 'pipeline_id'),
        ('users', 'id', 'tasks', 'assigned_to'),
        ('contacts', 'id', 'tasks', 'contact_id'),
        ('users', 'id', 'communications', 'user_id'),
        ('contacts', 'id', 'communications', 'contact_id')
    ]
    
    for parent_table, parent_col, child_table, child_col in relationships:
        try:
            # Check for child records that reference non-existent parent records
            cursor.execute(f"""
                SELECT c.{child_col}, COUNT(*) 
                FROM {child_table} c 
                LEFT JOIN {parent_table} p ON c.{child_col} = p.{parent_col} 
                WHERE p.{parent_col} IS NULL AND c.{child_col} IS NOT NULL
                GROUP BY c.{child_col}
            """)
            results = cursor.fetchall()
            
            if results:
                violations.append({
                    'parent_table': parent_table,
                    'child_table': child_table,
                    'child_column': child_col,
                    'orphaned_records': len(results),
                    'sample_ids': [r[0] for r in results[:5]]
                })
        except Exception as e:
            print(f"Error checking relationship {parent_table}.{parent_col} -> {child_table}.{child_col}: {e}")
    
    return violations

def check_null_constraints(cursor):
    """Check for NULL values in important columns that should be NOT NULL"""
    null_values = []
    
    # Critical columns that should not be NULL
    critical_columns = [
        ('users', ['email', 'first_name', 'last_name']),
        ('contacts', ['first_name', 'last_name']),
        ('pipeline_contacts', ['contact_id', 'stage_id']),
        ('pipeline_stages', ['name', 'pipeline_id']),
        ('pipelines', ['name']),
        ('tasks', ['title', 'status']),
        ('communications', ['type', 'contact_id'])
    ]
    
    for table, columns in critical_columns:
        for column in columns:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table} WHERE {column} IS NULL
                """)
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    cursor.execute(f"""
                        SELECT id FROM {table} WHERE {column} IS NULL LIMIT 5
                    """)
                    sample_ids = [r[0] for r in cursor.fetchall()]
                    
                    null_values.append({
                        'table': table,
                        'column': column,
                        'null_count': null_count,
                        'sample_ids': sample_ids
                    })
            except Exception as e:
                print(f"Error checking NULL values in {table}.{column}: {e}")
    
    return null_values

def check_data_integrity(cursor):
    """Perform specific data integrity checks"""
    integrity_issues = []
    
    # Check for duplicate emails in users table
    cursor.execute("""
        SELECT email, COUNT(*) 
        FROM users 
        GROUP BY email 
        HAVING COUNT(*) > 1
    """)
    duplicate_emails = cursor.fetchall()
    if duplicate_emails:
        integrity_issues.append({
            'issue_type': 'duplicate_user_emails',
            'count': len(duplicate_emails),
            'samples': [r[0] for r in duplicate_emails[:5]]
        })
    
    # Check for contacts that should be in at least one pipeline
    cursor.execute("""
        SELECT c.id, c.first_name, c.last_name 
        FROM contacts c 
        LEFT JOIN pipeline_contacts pc ON c.id = pc.contact_id 
        WHERE pc.id IS NULL
    """)
    orphaned_contacts = cursor.fetchall()
    if orphaned_contacts:
        integrity_issues.append({
            'issue_type': 'contacts_not_in_pipeline',
            'count': len(orphaned_contacts),
            'samples': [f"{r[0]} ({r[1]} {r[2]})" for r in orphaned_contacts[:5]]
        })
    
    # Check contacts with inconsistent data
    cursor.execute("""
        SELECT COUNT(*) 
        FROM contacts 
        WHERE (email IS NULL AND phone IS NULL) OR 
              (first_name IS NULL AND last_name IS NULL)
    """)
    incomplete_contacts = cursor.fetchone()[0]
    if incomplete_contacts > 0:
        integrity_issues.append({
            'issue_type': 'incomplete_contact_data',
            'count': incomplete_contacts
        })
    
    return integrity_issues

def generate_sql_fixes(cursor, violations, null_values, integrity_issues):
    """Generate SQL statements to fix common issues"""
    sql_fixes = []
    
    # Fix orphaned records by setting them to NULL where possible
    for violation in violations:
        sql_fixes.append(f"""
            -- Fix orphaned records in {violation['child_table']}
            UPDATE {violation['child_table']}
            SET {violation['child_column']} = NULL
            WHERE {violation['child_column']} NOT IN (
                SELECT id FROM {violation['parent_table']}
            ) AND {violation['child_column']} IS NOT NULL;
        """)
    
    # Fix NULL values in critical columns
    for null_issue in null_values:
        if null_issue['column'] in ('first_name', 'last_name'):
            sql_fixes.append(f"""
                -- Fix NULL {null_issue['column']} in {null_issue['table']}
                UPDATE {null_issue['table']}
                SET {null_issue['column']} = '(Unknown)'
                WHERE {null_issue['column']} IS NULL;
            """)
        elif null_issue['column'] == 'email':
            sql_fixes.append(f"""
                -- Fix NULL email in {null_issue['table']}
                UPDATE {null_issue['table']}
                SET email = CONCAT('unknown_', id, '@example.com')
                WHERE email IS NULL;
            """)
        elif null_issue['column'] == 'name':
            sql_fixes.append(f"""
                -- Fix NULL name in {null_issue['table']}
                UPDATE {null_issue['table']}
                SET name = CONCAT('Unnamed ', id)
                WHERE name IS NULL;
            """)
        elif null_issue['column'] == 'status':
            sql_fixes.append(f"""
                -- Fix NULL status in tasks
                UPDATE tasks
                SET status = 'incomplete'
                WHERE status IS NULL;
            """)
        elif null_issue['column'] == 'type':
            sql_fixes.append(f"""
                -- Fix NULL type in communications
                UPDATE communications
                SET type = 'other'
                WHERE type IS NULL;
            """)
    
    # Fix duplicate emails
    for issue in integrity_issues:
        if issue['issue_type'] == 'duplicate_user_emails':
            sql_fixes.append("""
                -- Identify duplicate emails (keep the most recent account)
                CREATE TEMP TABLE duplicate_emails AS
                SELECT id, email, date_created,
                       ROW_NUMBER() OVER (PARTITION BY email ORDER BY date_created DESC) as rn
                FROM users
                WHERE email IN (
                    SELECT email FROM users GROUP BY email HAVING COUNT(*) > 1
                );
                
                -- Update duplicate emails to make them unique
                UPDATE users
                SET email = CONCAT(email, '_', id)
                WHERE id IN (
                    SELECT id FROM duplicate_emails WHERE rn > 1
                );
                
                DROP TABLE IF EXISTS duplicate_emails;
            """)
    
    return sql_fixes

def main():
    print("Starting post-migration validation")
    
    # Connect to PostgreSQL database
    print(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(PG_CONNECTION)
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    try:
        # Get table counts
        print("\nChecking table row counts...")
        table_counts = get_table_counts(cursor)
        for table, count in table_counts.items():
            print(f"  - {table}: {count} rows")
        
        # Check for foreign key violations
        print("\nChecking for foreign key violations...")
        violations = check_foreign_keys(cursor)
        if violations:
            print(f"  Found {len(violations)} foreign key violations:")
            for v in violations:
                print(f"  - {v['child_table']}.{v['child_column']} -> {v['parent_table']}.id: {v['orphaned_records']} orphaned records")
                print(f"    Sample IDs: {v['sample_ids']}")
        else:
            print("  No foreign key violations found")
        
        # Check for NULL values in critical columns
        print("\nChecking for NULL values in critical columns...")
        null_values = check_null_constraints(cursor)
        if null_values:
            print(f"  Found {len(null_values)} columns with NULL values:")
            for nv in null_values:
                print(f"  - {nv['table']}.{nv['column']}: {nv['null_count']} NULL values")
                print(f"    Sample IDs: {nv['sample_ids']}")
        else:
            print("  No NULL values found in critical columns")
        
        # Check for data integrity issues
        print("\nChecking for data integrity issues...")
        integrity_issues = check_data_integrity(cursor)
        if integrity_issues:
            print(f"  Found {len(integrity_issues)} data integrity issues:")
            for issue in integrity_issues:
                print(f"  - {issue['issue_type']}: {issue['count']} issues")
                if 'samples' in issue:
                    print(f"    Samples: {issue['samples']}")
        else:
            print("  No data integrity issues found")
        
        # Generate SQL fixes
        if violations or null_values or integrity_issues:
            print("\nGenerating SQL fixes...")
            sql_fixes = generate_sql_fixes(cursor, violations, null_values, integrity_issues)
            
            # Write SQL fixes to file
            with open('data_fixes.sql', 'w') as f:
                f.write('-- SQL fixes for data integrity issues\n\n')
                f.write('BEGIN;\n\n')
                for sql in sql_fixes:
                    f.write(f"{sql}\n")
                f.write('\nCOMMIT;\n')
            
            print(f"  SQL fixes written to data_fixes.sql")
            print("  Review the SQL fixes before applying them to your database")
        
        print("\nValidation completed!")
    
    except Exception as e:
        print(f"Error during validation: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main() 