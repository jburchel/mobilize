"""Add created_at column to pipeline_stage_history table

Revision ID: pipeline_stage_history_fix_patched
Revises: add_main_pipeline_fields
Create Date: 2025-03-25 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'pipeline_stage_history_fix_patched'
down_revision = 'add_main_pipeline_fields'
branch_labels = None
depends_on = None

Base = declarative_base()

class PipelineStageHistory(Base):
    __tablename__ = 'pipeline_stage_history'
    id = sa.Column(sa.Integer, primary_key=True)
    moved_at = sa.Column(sa.DateTime)
    created_at = sa.Column(sa.DateTime, nullable=True)

def upgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [c['name'] for c in inspector.get_columns('pipeline_stage_history')]

    # Add created_at column if it doesn't exist
    if 'created_at' not in existing_columns:
        op.add_column('pipeline_stage_history', sa.Column('created_at', sa.DateTime(), nullable=True))
        
        # Create a session to copy data from moved_at to created_at
        Session = sessionmaker(bind=connection)
        session = Session()
        
        # Update created_at with moved_at values - use text() for raw SQL
        if 'moved_at' in existing_columns:
             session.execute(text("UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL"))
        
        # Set default for any NULL values in created_at
        session.execute(text("UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL"))
        
        session.commit()
        session.close()
        
        # Make the column non-nullable after populating (if needed, depends on model)
        # op.alter_column('pipeline_stage_history', 'created_at', nullable=False)

    # Add created_by_id column and FK if it doesn't exist
    if 'created_by_id' not in existing_columns:
        op.add_column('pipeline_stage_history', sa.Column('created_by_id', sa.Integer(), nullable=True))
        
        # Add foreign key if needed (handle potential errors if FK exists)
        try:
            op.create_foreign_key(
                'fk_pipeline_stage_history_created_by_id_users', 
                'pipeline_stage_history', 'users',
                ['created_by_id'], ['id']
            )
        except Exception as e:
            print(f"Could not create FK fk_pipeline_stage_history_created_by_id_users: {e}")
        
        # Copy data from moved_by_user_id to created_by_id if moved_by_user_id exists
        if 'moved_by_user_id' in existing_columns:
            Session = sessionmaker(bind=connection)
            session = Session()
            session.execute(text("UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL"))
            session.commit()
            session.close()
            # Make created_by_id non-nullable if desired
            # op.alter_column('pipeline_stage_history', 'created_by_id', nullable=False)

def downgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_columns = [column['name'] for column in inspector.get_columns('pipeline_stage_history')]
    
    # Drop created_by_id and its FK if they exist
    if 'created_by_id' in existing_columns:
        try:
            op.drop_constraint('fk_pipeline_stage_history_created_by_id_users', 'pipeline_stage_history', type_='foreignkey')
        except Exception as e:
            print(f"Could not drop FK constraint fk_pipeline_stage_history_created_by_id_users: {e}")
        op.drop_column('pipeline_stage_history', 'created_by_id')
    
    # Drop created_at column if it exists
    if 'created_at' in existing_columns:
        op.drop_column('pipeline_stage_history', 'created_at')

# Helper function to check if column exists (can be added if not present elsewhere)
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns 