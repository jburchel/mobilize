"""merge heads

Revision ID: b04398128fd1
Revises: 4cf4e63b4fc5, zz_add_sqlite_fixes
Create Date: 2025-05-29 09:30:48.748562

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b04398128fd1'
down_revision = ('4cf4e63b4fc5', 'zz_add_sqlite_fixes')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
