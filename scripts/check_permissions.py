#!/usr/bin/env python3
"""
Script to check permission structure.
"""

import os
import sys
import inspect
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app import create_app, db
from app.models.permission import Permission

def check_permissions():
    """Check permission model structure and data."""
    print("Checking permission model structure and data...")
    
    try:
        # Create application context
        app = create_app()
        
        with app.app_context():
            # Print Permission model structure
            print("\n=== Permission Model Structure ===")
            print(f"Permission class: {Permission}")
            
            # Print Permission attributes
            print("\nAttributes:")
            for attr in dir(Permission):
                if not attr.startswith('_'):
                    print(f"  {attr}")
            
            # Print Permission columns
            print("\nColumns:")
            if hasattr(Permission, '__table__'):
                for column in Permission.__table__.columns:
                    print(f"  {column.name}: {column.type}")
            else:
                print("  No __table__ attribute found")
            
            # Check if Permission model has user_id attribute
            print("\nChecking for user_id:")
            if hasattr(Permission, 'user_id'):
                print(f"  user_id attribute exists: {getattr(Permission, 'user_id')}")
            else:
                print("  No user_id attribute found")
            
            # Try to get all permissions
            try:
                permissions = db.session.query(Permission).all()
                print(f"\nFound {len(permissions)} permissions")
                
                # Print first 5 permissions
                for i, permission in enumerate(permissions[:5]):
                    print(f"\nPermission {i+1}:")
                    for column in Permission.__table__.columns:
                        value = getattr(permission, column.name)
                        print(f"  {column.name}: {value}")
            except Exception as e:
                print(f"\nError querying permissions: {str(e)}")
            
            # Try a raw SQL query
            try:
                result = db.session.execute(db.text("SELECT * FROM permissions LIMIT 5;"))
                rows = result.fetchall()
                print(f"\nRaw SQL found {len(rows)} permissions")
                
                # Get column names
                if rows:
                    columns = result.keys()
                    print(f"Columns: {', '.join(columns)}")
                    
                    # Print permissions
                    for i, row in enumerate(rows):
                        print(f"\nPermission {i+1} (raw):")
                        for j, column in enumerate(columns):
                            print(f"  {column}: {row[j]}")
            except Exception as e:
                print(f"\nError running raw SQL: {str(e)}")
    
    except Exception as e:
        print(f"\n❌ Error checking permissions: {str(e)}")
        print("\nFull error traceback:")
        import traceback
        print(traceback.format_exc())
        return

if __name__ == "__main__":
    check_permissions() 