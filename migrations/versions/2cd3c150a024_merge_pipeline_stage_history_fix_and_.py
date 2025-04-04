"""merge pipeline_stage_history_fix and eeb2b80b5f20

Revision ID: 2cd3c150a024
Revises: eeb2b80b5f20, pipeline_stage_history_fix
Create Date: 2025-04-04 14:50:08.967878

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2cd3c150a024'
down_revision = ('eeb2b80b5f20', 'pipeline_stage_history_fix')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
