import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db

app = create_app()
with app.app_context():
    tables = [t.name for t in db.metadata.tables.values()]
    print("Database Tables:")
    for table in tables:
        print(f"- {table}")
