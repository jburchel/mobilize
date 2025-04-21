"""
PostgreSQL Migration Test - Final Version

This script connects to a PostgreSQL database and generates the SQL that would be executed
for the latest migration. This is useful for testing PostgreSQL compatibility before
applying migrations to the production database.
"""

import os
import sys
import io
import importlib.util
from logging import getLogger
from sqlalchemy import create_engine, text
from alembic.operations import Operations
from alembic.migration import MigrationContext
from contextlib import contextmanager

# Setup logging
logger = getLogger(__name__)

def find_latest_migration():
    """Find the latest migration file in the migrations/versions directory."""
    migrations_dir = os.path.join('migrations', 'versions')
    try:
        migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py')]
        if not migration_files:
            print("No migration files found in migrations/versions directory.")
            return None
            
        # Sort the files to get the latest one
        latest_migration_file = sorted(migration_files)[-1]
        print(f"Using latest migration file: {latest_migration_file}")
        
        return os.path.join(migrations_dir, latest_migration_file), latest_migration_file[:-3]
    except Exception as e:
        print(f"Error finding migration files: {e}")
        return None

def import_migration_module(file_path, module_name):
    """Dynamically import the migration module."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        migration_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration_module)
        
        print(f"Successfully imported migration module: {module_name}")
        return migration_module
    except Exception as e:
        print(f"Error importing migration module: {e}")
        import traceback
        traceback.print_exc()
        return None

class MockSession:
    """A mock SQLAlchemy session that records SQL commands."""
    def __init__(self):
        self.recorded_sql = []
    
    def execute(self, statement, *args, **kwargs):
        """Record SQL statement instead of executing it."""
        # For text objects, get the SQL text
        if hasattr(statement, 'text'):
            sql = statement.text
        else:
            sql = str(statement)
        
        # Add parameters if available
        params = kwargs.get('params', {})
        if params:
            sql += f" (params: {params})"
        
        self.recorded_sql.append(sql)
        print(f"SQL: {sql}")
        
        # Return a mock result that can be used in a with statement
        class MockResult:
            def __enter__(self):
                return self
            
            def __exit__(self, *args):
                pass
            
            def fetchall(self):
                return []
            
            def fetchone(self):
                return None
        
        return MockResult()
    
    def commit(self):
        """Mock commit method."""
        pass
    
    def close(self):
        """Mock close method."""
        pass
    
    def get_sql_commands(self):
        """Return all recorded SQL commands."""
        return self.recorded_sql

@contextmanager
def capture_output():
    """Capture stdout to get the SQL commands."""
    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer
    try:
        yield buffer
    finally:
        sys.stdout = old_stdout

def test_migration(db_url):
    """Test the migration against PostgreSQL and return the SQL that would be executed."""
    migration_info = find_latest_migration()
    if not migration_info:
        return "No migration files found."
        
    file_path, module_name = migration_info
    migration_module = import_migration_module(file_path, module_name)
    if not migration_module:
        return "Failed to import migration module."
    
    with capture_output() as buffer:
        try:
            # Create engine
            engine = create_engine(db_url, echo=True)
            
            # Test connection
            with engine.connect() as conn:
                print("Successfully connected to PostgreSQL database")
                
                # Create a context that will collect SQL instead of executing it
                ctx = MigrationContext.configure(
                    conn,
                    opts={
                        'as_sql': True,
                        'target_metadata': None
                    }
                )
                
                # Create operation object
                op = Operations(ctx)
                
                # Create a mock session
                mock_session = MockSession()
                
                # Make the mock session available to the migration
                original_session = None
                if hasattr(migration_module, 'session'):
                    original_session = migration_module.session
                migration_module.session = mock_session
                
                # Run the upgrade function
                print("\n--- SQL COMMANDS THAT WOULD BE EXECUTED ---\n")
                
                # Check if upgrade accepts the op parameter
                import inspect
                sig = inspect.signature(migration_module.upgrade)
                if len(sig.parameters) > 0:
                    migration_module.upgrade(op)
                else:
                    # Set global op variable that the migration can use
                    migration_module.__dict__['op'] = op
                    migration_module.upgrade()
                
                # Print SQL commands from operations
                for sql in mock_session.get_sql_commands():
                    print(f"Session SQL: {sql}")
                
                # Restore original session if needed
                if original_session is not None:
                    migration_module.session = original_session
                
        except Exception as e:
            print(f"Error during migration test: {e}")
            import traceback
            traceback.print_exc()
    
    return buffer.getvalue()

if __name__ == "__main__":
    # Default database URL for Supabase PostgreSQL using connection pooler
    db_url = "postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
    
    # Allow overriding the database URL via environment variable
    if 'DATABASE_URL' in os.environ:
        db_url = os.environ['DATABASE_URL']
        print(f"Using database URL from environment: {db_url}")
    
    # Run the test
    result = test_migration(db_url)
    
    # Print the result
    print("\n=== MIGRATION TEST RESULTS ===\n")
    print(result) 