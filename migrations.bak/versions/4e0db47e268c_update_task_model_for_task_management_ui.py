"""Update Task model for task management UI

Revision ID: 4e0db47e268c
Revises: bbda44b09940
Create Date: 2025-03-21 08:45:51.891509

"""
from alembic import op
import sqlalchemy as sa
from alembic.operations import ops

# revision identifiers, used by Alembic.
revision = '4e0db47e268c'
down_revision = 'bbda44b09940'
branch_labels = None
depends_on = None


def upgrade():
    # ### Using batch mode for SQLite compatibility ###
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('reminder_1_day', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('reminder_2_hours', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('completed_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('completion_notes', sa.Text(), nullable=True))
        # Create the foreign key after dropping the old one
        if op.get_bind().dialect.name != 'sqlite':  # Skip for SQLite
            batch_op.drop_constraint(None, type_='foreignkey')
            batch_op.create_foreign_key(None, 'users', ['created_by'], ['id'])
            batch_op.drop_column('user_id')
        else:
            # For SQLite, we can't drop and create constraints, we just add the column
            # and will set up relationships in the model
            pass
    
    # For SQLite, let's just add a separate operation to drop the user_id column
    if op.get_bind().dialect.name == 'sqlite':
        with op.batch_alter_table('tasks', schema=None) as batch_op:
            batch_op.drop_column('user_id')


def downgrade():
    # ### Using batch mode for SQLite compatibility ###
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), nullable=True))
        if op.get_bind().dialect.name != 'sqlite':  # Skip for SQLite
            batch_op.drop_constraint(None, type_='foreignkey')
            batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])
        batch_op.drop_column('completion_notes')
        batch_op.drop_column('completed_date')
        batch_op.drop_column('reminder_2_hours')
        batch_op.drop_column('reminder_1_day')
        batch_op.drop_column('created_by')
