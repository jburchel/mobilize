from sqlalchemy import create_engine, text, inspect
import sys
import os
import importlib.util
from alembic.operations import ops, Operations
from alembic.migration import MigrationContext

# Create a modified version of the migration function that only collects SQL
def create_sql_only_migration():
    # Create a list to collect SQL statements
    sql_statements = []
    
    # Define a custom upgrade function that captures SQL
    def collect_sql_upgrade():
        # Add created_at column if it doesn't exist
        sql_statements.append("ALTER TABLE pipeline_stage_history ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE;")
        
        # Update created_at with moved_at values
        sql_statements.append("UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL;")
        
        # Set default for any NULL values in created_at
        sql_statements.append("UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;")
        
        # Add created_by_id column
        sql_statements.append("ALTER TABLE pipeline_stage_history ADD COLUMN created_by_id INTEGER;")
        
        # Add foreign key
        sql_statements.append("ALTER TABLE pipeline_stage_history ADD CONSTRAINT fk_pipeline_stage_history_created_by_id_users FOREIGN KEY (created_by_id) REFERENCES users (id);")
        
        # Copy data from moved_by_user_id to created_by_id
        sql_statements.append("UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL;")
    
    return collect_sql_upgrade, sql_statements

try:
    # Create a connection to PostgreSQL using the Supavisor Connection Pooler
    db_url = "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    engine = create_engine(db_url, echo=True)
    
    # Test the connection
    with engine.connect() as conn:
        print("Successfully connected to PostgreSQL database")
        
        # Check if the pipeline_stage_history table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if 'pipeline_stage_history' in tables:
            print(f"Table 'pipeline_stage_history' exists in the database")
            
            # Get columns to simulate the inspector in the migration
            columns = [column['name'] for column in inspector.get_columns('pipeline_stage_history')]
            print(f"Columns in pipeline_stage_history: {columns}")
        else:
            print(f"Table 'pipeline_stage_history' does not exist in the database")
        
        # Create the SQL-only migration and execute it
        upgrade_fn, sql_statements = create_sql_only_migration()
        upgrade_fn()
        
        # Print the SQL statements
        print("\n--- SQL COMMANDS THAT WOULD BE EXECUTED ---\n")
        for sql in sql_statements:
            print(sql)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 