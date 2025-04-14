"""add google_meet_link to communications

Revision ID: add_google_meet_link
Revises: 
Create Date: 2025-04-14 13:10:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = 'add_google_meet_link'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Get the database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Get existing columns in the communications table
    columns = [column['name'] for column in inspector.get_columns('communications')]
    
    # Add google_meet_link column to communications table if it doesn't exist
    if 'google_meet_link' not in columns:
        op.add_column('communications', sa.Column('google_meet_link', sa.String(), nullable=True))
    
    # Add google_calendar_event_id column if it doesn't exist
    if 'google_calendar_event_id' not in columns:
        op.add_column('communications', sa.Column('google_calendar_event_id', sa.String(), nullable=True))


def downgrade():
    # Get the database connection
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    
    # Get existing columns in the communications table
    columns = [column['name'] for column in inspector.get_columns('communications')]
    
    # Remove the columns if they exist
    if 'google_meet_link' in columns:
        op.drop_column('communications', 'google_meet_link')
    
    if 'google_calendar_event_id' in columns:
        op.drop_column('communications', 'google_calendar_event_id') 