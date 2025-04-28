"""Replace reminder booleans with reminder_option dropdown

Revision ID: 00a6f3565d53
Revises: ab1e0d1b31aa
Create Date: 2025-03-21 16:04:20.895006

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '00a6f3565d53'
down_revision = 'ab1e0d1b31aa'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch mode, but check for column existence before dropping
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        if column_exists('tasks', 'reminder_time'):
            batch_op.drop_column('reminder_time')
        if column_exists('tasks', 'reminder_1_day'):
            batch_op.drop_column('reminder_1_day')
        if column_exists('tasks', 'reminder_2_hours'):
            batch_op.drop_column('reminder_2_hours')
    # ### end Alembic commands ###


def downgrade():
    # Use batch mode, but check before adding back
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        if not column_exists('tasks', 'reminder_2_hours'):
            batch_op.add_column(sa.Column('reminder_2_hours', sa.BOOLEAN(), nullable=True))
        if not column_exists('tasks', 'reminder_1_day'):
            batch_op.add_column(sa.Column('reminder_1_day', sa.BOOLEAN(), nullable=True))
        # Assuming reminder_time was VARCHAR if it existed
        if not column_exists('tasks', 'reminder_time'):
            batch_op.add_column(sa.Column('reminder_time', sa.VARCHAR(), nullable=True))
    # ### end Alembic commands ###

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
