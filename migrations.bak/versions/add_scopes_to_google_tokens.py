"""Add scopes to google tokens

Revision ID: add_scopes_to_google_tokens
Revises: 8ed80b7eaa73
Create Date: 2023-05-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_scopes_to_google_tokens'
down_revision = '8ed80b7eaa73'
branch_labels = None
depends_on = None


def upgrade():
    # This is a dummy migration to fix the migration history
    pass


def downgrade():
    # This is a dummy migration to fix the migration history
    pass 