import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy.sql import text

app = create_app()
with app.app_context():
    tables = [t.name for t in db.metadata.tables.values()]
    print("Database Schema Inspection:")
    for table in tables:
        print(f"\nTable: {table}")
        try:
            result = db.session.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :table_name"), {'table_name': table})
            for row in result:
                print(f"- {row.column_name}: {row.data_type}")
        except Exception as e:
            print(f"Error inspecting table {table}: {str(e)}")
