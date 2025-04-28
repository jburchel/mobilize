"""SQLite catch-up fixes

Revision ID: zz_add_sqlite_fixes
Revises: modified_pg_migration
Create Date: 2025-04-25 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'zz_add_sqlite_fixes'
down_revision = 'modified_pg_migration'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Only run on SQLite local dev
    if bind.dialect.name != 'sqlite':
        return
    inspector = inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('tasks')]
    if 'type' not in cols:
        op.add_column('tasks', sa.Column('type', sa.String(length=50), nullable=False, server_default='general'))


def downgrade():
    # Only apply on SQLite
    bind = op.get_bind()
    if bind.dialect.name != 'sqlite':
        return
    inspector = inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('tasks')]
    if 'type' in cols:
        op.drop_column('tasks', 'type') 