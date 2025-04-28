"""merge_heads

Revision ID: b604f5030685
Revises: add_missing_person_fields, add_scopes_to_google_tokens
Create Date: 2025-04-17 16:18:02.526819

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b604f5030685'
down_revision = ('add_missing_person_fields', 'add_scopes_to_google_tokens')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
