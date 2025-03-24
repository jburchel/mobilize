"""add person_id to users table

Revision ID: 9761ea2e6b58
Revises: 4cb401521a9e
Create Date: 2025-03-24 09:07:40.474726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9761ea2e6b58'
down_revision = '4cb401521a9e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('person_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_person_id', 'people', ['person_id'], ['id'])


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_person_id', type_='foreignkey')
        batch_op.drop_column('person_id')
