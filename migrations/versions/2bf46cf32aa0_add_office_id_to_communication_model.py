"""Add office_id to Communication model

Revision ID: 2bf46cf32aa0
Revises: 078ff034365a
Create Date: 2024-03-20 10:58:07.546726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bf46cf32aa0'
down_revision = '078ff034365a'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new table with the updated schema
    with op.batch_alter_table('communications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('office_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_communications_office_id_offices', 'offices', ['office_id'], ['id'])


def downgrade():
    # Remove the office_id column and its foreign key
    with op.batch_alter_table('communications', schema=None) as batch_op:
        batch_op.drop_constraint('fk_communications_office_id_offices', type_='foreignkey')
        batch_op.drop_column('office_id')
