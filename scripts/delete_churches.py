#!/usr/bin/env python3
"""Script to delete all churches from the database."""

from pathlib import Path
import sys

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.church import Church

def delete_churches():
    """Delete all churches from the database."""
    print("Deleting all churches...")
    app = create_app()
    with app.app_context():
        Church.query.delete()
        db.session.commit()
        print("✅ All churches deleted successfully.")

if __name__ == "__main__":
    delete_churches() 