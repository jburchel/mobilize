"""Add user_id to Contact model

Revision ID: bbda44b09940
Revises: 2bf46cf32aa0
Create Date: 2025-03-20 11:02:45.372389

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbda44b09940'
down_revision = '2bf46cf32aa0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_contacts_user_id_users', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.drop_constraint('fk_contacts_user_id_users', type_='foreignkey')
        batch_op.drop_column('user_id')
    # ### end Alembic commands ###
