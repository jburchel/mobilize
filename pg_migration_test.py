from app import create_app
from flask_migrate import Migrate
from sqlalchemy import create_engine
from app.extensions import db
import io
import sys

# Capture stdout to get the SQL commands
old_stdout = sys.stdout
buffer = io.StringIO()
sys.stdout = buffer

# Create a test app with PostgreSQL URL
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://dummy_user:dummy_password@dummy_host:5432/dummy_db'

with app.app_context():
    # Import the migration script
    from migrations.versions.b604f5030685_merge_heads import upgrade as upgrade_merge
    # Need to use importlib for filenames with numbers
    import importlib.util
    import os
    
    # Find the production ready schema migration file
    migration_dir = os.path.join('migrations', 'versions')
    for filename in os.listdir(migration_dir):
        if 'production_ready_schema' in filename:
            production_schema_file = filename.split('.')[0]
            
    # Import the production ready schema migration
    spec = importlib.util.spec_from_file_location(
        production_schema_file, 
        os.path.join(migration_dir, f"{production_schema_file}.py")
    )
    pg_compat_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pg_compat_module)
    upgrade_pg_compat = pg_compat_module.upgrade
    
    # Setup mock Alembic operations to log SQL instead of executing
    from alembic.operations import Operations
    from alembic.migration import MigrationContext
    
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    conn = engine.connect()
    
    # Configure logging context
    context = MigrationContext.configure(
        connection=conn,
        opts={
            'as_sql': True,
            'dialect_opts': {
                'paramstyle': 'named'
            }
        }
    )
    
    # Create operational facade
    op = Operations(context)
    
    # Run the upgrade function
    print("-- SQL for upgrade_merge:")
    try:
        upgrade_merge(op)
    except Exception as e:
        print(f"Error in merge upgrade: {e}")
    
    print("\n-- SQL for upgrade_pg_compat:")
    try:
        upgrade_pg_compat(op)
    except Exception as e:
        print(f"Error in pg_compat upgrade: {e}")

# Restore stdout
sys.stdout = old_stdout

# Print the SQL commands
print(buffer.getvalue()) 