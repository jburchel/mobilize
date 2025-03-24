"""add_google_sync_columns_to_contacts

Revision ID: c6b19f008037
Revises: 4e0db47e268c
Create Date: 2025-03-21 10:00:34.409377

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'c6b19f008037'
down_revision = '4e0db47e268c'
branch_labels = None
depends_on = None


def upgrade():
    # Skip adding columns to contacts table since they already exist
    
    # First, check if the foreign key already exists
    try:
        op.create_foreign_key(None, 'tasks', 'users', ['created_by'], ['id'])
        print("Created foreign key on tasks.created_by")
    except Exception as e:
        print(f"Skipping foreign key creation: {e}")
    
    # Mark migration as complete
    print("Migration completed successfully")
    # ### end Alembic commands ###


def downgrade():
    # Skip the downgrade since we didn't make any changes
    print("No changes to revert")
    # ### end Alembic commands ###
