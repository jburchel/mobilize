from sqlalchemy import create_engine, text
import io
import sys
import os
import importlib.util
from alembic.operations import ops, Operations
from alembic.migration import MigrationContext

# Capture stdout to get the SQL commands
old_stdout = sys.stdout
buffer = io.StringIO()
sys.stdout = buffer

try:
    # Use our patched migration file
    file_path = os.path.join('migrations', 'versions', 'pipeline_stage_history_fix_patched.py')
    module_name = 'pipeline_stage_history_fix_patched'
    
    # Dynamically import the migration file
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    print("Successfully imported patched migration module")
    
    # Create a connection to PostgreSQL using the Supavisor Connection Pooler
    db_url = "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    engine = create_engine(db_url, echo=True)
    
    # Create a connection and set up the context
    with engine.connect() as conn:
        print("Successfully connected to PostgreSQL database")
        
        # Create a context that will collect SQL instead of executing it
        ctx = MigrationContext.configure(
            conn,
            opts={
                'as_sql': True,  # Generate SQL instead of executing
                'target_metadata': None  # We're not using the metadata here
            }
        )
        
        # Create operation object and make it available to the migration
        op = Operations(ctx)
        migration_module.op = op
        
        # Get the SQL commands that would be run
        print("\n--- SQL COMMANDS THAT WOULD BE EXECUTED ---\n")
        migration_module.upgrade()
        
        # Print the generated SQL
        print("\n--- GENERATED SQL FROM MIGRATION ---\n")
        print(ctx.sql.compile(dialect=engine.dialect))
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Restore stdout
sys.stdout = old_stdout

# Print the SQL commands
print(buffer.getvalue()) 