#!/usr/bin/env python
"""
Script to directly update the database schema for pipeline tables.
This script is needed when Flask-Migrate can't handle the migrations directly.
"""
import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app, db
from app.models import PipelineStage, PipelineContact, PipelineStageHistory
import sqlalchemy as sa

def execute_sql(conn, sql, params=None):
    """Execute SQL with optional parameters and return results."""
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        conn.commit()
        return cursor.fetchall()
    except Exception as e:
        print(f"Error executing SQL: {e}")
        print(f"SQL: {sql}")
        if params:
            print(f"Params: {params}")
        return None

def table_exists(conn, table_name):
    """Check if a table exists in the database."""
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
    result = execute_sql(conn, sql, (table_name,))
    return bool(result)

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table."""
    sql = f"PRAGMA table_info({table_name});"
    columns = execute_sql(conn, sql)
    return any(col[1] == column_name for col in columns)

def get_table_columns(conn, table_name):
    """Get all columns in a table."""
    sql = f"PRAGMA table_info({table_name});"
    return execute_sql(conn, sql)

def update_pipeline_schema():
    """Update the pipeline tables schema directly with SQL."""
    print("Starting direct schema update for pipeline tables...")
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Get database path
        db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_path.startswith('sqlite:///'):
            db_path = db_path[10:]  # Remove 'sqlite:///'
        else:
            print(f"Unsupported database type: {db_path}")
            return False
        
        print(f"Using database: {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        
        try:
            # Check if tables exist
            pipeline_stages_exists = table_exists(conn, 'pipeline_stages')
            pipeline_contacts_exists = table_exists(conn, 'pipeline_contacts')
            
            if not pipeline_stages_exists or not pipeline_contacts_exists:
                print("Pipeline tables don't exist yet. No schema changes needed.")
                return False
            
            # Get current columns
            pipeline_stages_columns = get_table_columns(conn, 'pipeline_stages')
            pipeline_contacts_columns = get_table_columns(conn, 'pipeline_contacts')
            
            print("Current pipeline_stages columns:")
            for col in pipeline_stages_columns:
                print(f"  {col[1]} ({col[2]})")
                
            print("Current pipeline_contacts columns:")
            for col in pipeline_contacts_columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Check if color column exists in pipeline_stages
            color_exists = column_exists(conn, 'pipeline_stages', 'color')
            if not color_exists:
                print("Adding color column to pipeline_stages...")
                sql = "ALTER TABLE pipeline_stages ADD COLUMN color TEXT DEFAULT '#3498db';"
                execute_sql(conn, sql)
                print("Color column added to pipeline_stages.")
            else:
                print("Color column already exists in pipeline_stages.")
            
            # Check if we need to add current_stage_id to pipeline_contacts
            current_stage_id_exists = column_exists(conn, 'pipeline_contacts', 'current_stage_id')
            stage_id_exists = column_exists(conn, 'pipeline_contacts', 'stage_id')
            
            if stage_id_exists and not current_stage_id_exists:
                print("Renaming stage_id to current_stage_id in pipeline_contacts...")
                # SQLite doesn't support column renaming directly, we need to do it in multiple steps
                
                # 1. Create a temporary table
                execute_sql(conn, """
                CREATE TABLE pipeline_contacts_temp (
                    id INTEGER PRIMARY KEY,
                    contact_id INTEGER NOT NULL,
                    pipeline_id INTEGER NOT NULL,
                    current_stage_id INTEGER NOT NULL,
                    entered_at DATETIME,
                    last_updated DATETIME,
                    FOREIGN KEY (contact_id) REFERENCES contacts (id),
                    FOREIGN KEY (pipeline_id) REFERENCES pipelines (id),
                    FOREIGN KEY (current_stage_id) REFERENCES pipeline_stages (id)
                );
                """)
                
                # 2. Copy data from the original table, mapping stage_id to current_stage_id
                execute_sql(conn, """
                INSERT INTO pipeline_contacts_temp (id, contact_id, pipeline_id, current_stage_id, entered_at, last_updated)
                SELECT id, contact_id, pipeline_id, stage_id, 
                       COALESCE(entered_at, created_at), 
                       COALESCE(last_updated, updated_at)
                FROM pipeline_contacts;
                """)
                
                # 3. Drop the original table
                execute_sql(conn, "DROP TABLE pipeline_contacts;")
                
                # 4. Rename the temporary table to the original name
                execute_sql(conn, "ALTER TABLE pipeline_contacts_temp RENAME TO pipeline_contacts;")
                
                print("Renamed stage_id to current_stage_id in pipeline_contacts.")
            elif not stage_id_exists and not current_stage_id_exists:
                print("ERROR: Neither stage_id nor current_stage_id exists in pipeline_contacts!")
                return False
            elif current_stage_id_exists:
                print("current_stage_id already exists in pipeline_contacts.")
            
            # Create entered_at and last_updated if needed
            entered_at_exists = column_exists(conn, 'pipeline_contacts', 'entered_at')
            last_updated_exists = column_exists(conn, 'pipeline_contacts', 'last_updated')
            
            if not entered_at_exists:
                print("Adding entered_at column to pipeline_contacts...")
                sql = "ALTER TABLE pipeline_contacts ADD COLUMN entered_at DATETIME DEFAULT CURRENT_TIMESTAMP;"
                execute_sql(conn, sql)
                print("entered_at column added to pipeline_contacts.")
            
            if not last_updated_exists:
                print("Adding last_updated column to pipeline_contacts...")
                sql = "ALTER TABLE pipeline_contacts ADD COLUMN last_updated DATETIME DEFAULT CURRENT_TIMESTAMP;"
                execute_sql(conn, sql)
                print("last_updated column added to pipeline_contacts.")
            
            # Add missing indexes if needed
            print("Adding indexes for performance...")
            execute_sql(conn, "CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_pipeline_id ON pipeline_contacts (pipeline_id);")
            execute_sql(conn, "CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_contact_id ON pipeline_contacts (contact_id);")
            execute_sql(conn, "CREATE INDEX IF NOT EXISTS idx_pipeline_contacts_current_stage_id ON pipeline_contacts (current_stage_id);")
            execute_sql(conn, "CREATE INDEX IF NOT EXISTS idx_pipeline_stages_pipeline_id ON pipeline_stages (pipeline_id);")
            
            print("Schema update completed successfully.")
            return True
            
        except Exception as e:
            print(f"Error updating schema: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            conn.close()

if __name__ == "__main__":
    success = update_pipeline_schema()
    sys.exit(0 if success else 1) 