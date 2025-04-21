from app import create_app
from flask_migrate import Migrate
from sqlalchemy import create_engine
from app.extensions import db
import io
import sys
import os
import importlib.util
from logging import getLogger
from alembic.operations import ops, Operations
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext

# Setup logging
logger = getLogger(__name__)

# Capture stdout to get the SQL commands
old_stdout = sys.stdout
buffer = io.StringIO()
sys.stdout = buffer

# Find the latest migration file
migrations_dir = os.path.join('migrations', 'versions')
migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
if not migration_files:
    print("No migration files found in migrations/versions directory.")
    sys.exit(1)

# Sort the files to get the latest one (assuming filenames have a timestamp/version prefix)
latest_migration_file = sorted(migration_files)[-1]
print(f"Using latest migration file: {latest_migration_file}")

# Dynamically import the migration file
file_path = os.path.join(migrations_dir, latest_migration_file)
module_name = latest_migration_file[:-3]  # Remove .py extension

try:
    # Handle filenames with numbers
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    print("Successfully imported migration module")
    
    # Create a connection to PostgreSQL (this will not actually connect yet)
    # Using the production connection string
    db_url = "postgresql://postgres:Fruitin2025!@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres"
    
    engine = create_engine(db_url, echo=True)
    
    # Setup mock context for operations
    def do_upgrade(rev, context):
        return migration_module.upgrade(op)
        
    # Create a connection and set up the context
    try:
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
            
            # Create operation object
            op = Operations(ctx)
            
            # Get the SQL commands that would be run
            print("\n--- SQL COMMANDS THAT WOULD BE EXECUTED ---\n")
            sql_commands = do_upgrade(None, ctx)
            print(sql_commands if sql_commands else "No SQL commands would be executed.")
    except Exception as e:
        print(f"Database connection or SQL generation error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"Script error: {e}")
    import traceback
    traceback.print_exc()

# Restore stdout
sys.stdout = old_stdout

# Print the SQL commands
print(buffer.getvalue()) 