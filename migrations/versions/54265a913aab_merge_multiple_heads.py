"""merge_multiple_heads

Revision ID: 54265a913aab
Revises: add_google_meet_link, eeb2b80b5f20, pipeline_stage_history_fix
Create Date: 2025-04-14 14:25:09.969481

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54265a913aab'
down_revision = ('add_google_meet_link', 'eeb2b80b5f20', 'pipeline_stage_history_fix')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
