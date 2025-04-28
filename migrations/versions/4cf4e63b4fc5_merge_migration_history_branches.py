"""Merge migration history branches

Revision ID: 4cf4e63b4fc5
Revises: ('modified_pg_migration', 'pipeline_stage_history_fix_patched')
Create Date: 2025-04-25 15:11:10.894307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4cf4e63b4fc5'
down_revision = ('modified_pg_migration', 'pipeline_stage_history_fix_patched')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
