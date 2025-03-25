"""Add created_at column to pipeline_stage_history table

Revision ID: pipeline_stage_history_fix
Revises: add_main_pipeline_fields
Create Date: 2025-03-25 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'pipeline_stage_history_fix'
down_revision = 'add_main_pipeline_fields'
branch_labels = None
depends_on = None

Base = declarative_base()

class PipelineStageHistory(Base):
    __tablename__ = 'pipeline_stage_history'
    id = sa.Column(sa.Integer, primary_key=True)
    moved_at = sa.Column(sa.DateTime)
    created_at = sa.Column(sa.DateTime)

def upgrade():
    # Add created_at column if it doesn't exist
    op.add_column('pipeline_stage_history', sa.Column('created_at', sa.DateTime(), nullable=True))
    
    # Create a session to copy data from moved_at to created_at
    connection = op.get_bind()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    # Update created_at with moved_at values
    session.execute("UPDATE pipeline_stage_history SET created_at = moved_at WHERE moved_at IS NOT NULL")
    
    # Set default for any NULL values in created_at
    session.execute("UPDATE pipeline_stage_history SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    
    # Check if created_by_id column exists, if not, add it
    inspector = sa.inspect(connection)
    columns = [column['name'] for column in inspector.get_columns('pipeline_stage_history')]
    
    if 'created_by_id' not in columns:
        op.add_column('pipeline_stage_history', sa.Column('created_by_id', sa.Integer(), nullable=True))
        
        # Add foreign key if needed
        op.create_foreign_key(
            'fk_pipeline_stage_history_created_by_id_users', 
            'pipeline_stage_history', 'users',
            ['created_by_id'], ['id']
        )
        
        # Copy data from moved_by_user_id to created_by_id if that column exists
        if 'moved_by_user_id' in columns:
            session.execute("UPDATE pipeline_stage_history SET created_by_id = moved_by_user_id WHERE moved_by_user_id IS NOT NULL")
    
    session.commit()
    session.close()

def downgrade():
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [column['name'] for column in inspector.get_columns('pipeline_stage_history')]
    
    # Drop created_by_id if we added it
    if 'created_by_id' in columns and 'moved_by_user_id' in columns:
        op.drop_constraint('fk_pipeline_stage_history_created_by_id_users', 'pipeline_stage_history', type_='foreignkey')
        op.drop_column('pipeline_stage_history', 'created_by_id')
    
    # Drop created_at column
    op.drop_column('pipeline_stage_history', 'created_at') 