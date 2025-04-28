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
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    # Check for columns *before* batch for SQLite
    created_by_exists_sqlite = is_sqlite and column_exists('tasks', 'created_by')
    user_id_exists_sqlite = is_sqlite and column_exists('tasks', 'user_id')

    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # Add columns if they don't exist
        if not column_exists('tasks', 'created_by'):
            batch_op.add_column(sa.Column('created_by', sa.Integer(), nullable=True))
        if not column_exists('tasks', 'reminder_1_day'):
            batch_op.add_column(sa.Column('reminder_1_day', sa.Boolean(), nullable=True))
        if not column_exists('tasks', 'reminder_2_hours'):
            batch_op.add_column(sa.Column('reminder_2_hours', sa.Boolean(), nullable=True))
        if not column_exists('tasks', 'completed_date'):
            batch_op.add_column(sa.Column('completed_date', sa.DateTime(), nullable=True))
        if not column_exists('tasks', 'completion_notes'):
            batch_op.add_column(sa.Column('completion_notes', sa.Text(), nullable=True))

        # Foreign key and column drop logic (handle dialect differences)
        if not is_sqlite:
            # Attempt to drop old FK if it exists (using a generic name might fail if specific name was used)
            # This part is risky if the old FK name isn't known or consistent.
            # Consider commenting out if it causes issues.
            # try:
            #     batch_op.drop_constraint(None, type_='foreignkey') 
            # except Exception as e:
            #     print(f"Could not drop potentially existing FK: {e}")

            if column_exists('tasks', 'created_by'): # Only create FK if column exists
                batch_op.create_foreign_key('fk_tasks_created_by_users', 'users', ['created_by'], ['id'])
            
            if column_exists('tasks', 'user_id'): # Only drop if it exists
                batch_op.drop_column('user_id')
        else:
             # Explicitly drop user_id for SQLite outside batch if it exists, as batch drop might fail
             # We already checked user_id_exists_sqlite before the batch
             pass # We will handle SQLite drop after batch
    
    # Handle SQLite specific drop outside batch
    if is_sqlite and user_id_exists_sqlite:
         # Need a new batch context to drop column in SQLite
         with op.batch_alter_table('tasks', schema=None) as batch_op_sqlite_drop:
            batch_op_sqlite_drop.drop_column('user_id')


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Use batch mode for downgrade as well
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # Add user_id back if it doesn't exist
        if not column_exists('tasks', 'user_id'):
            batch_op.add_column(sa.Column('user_id', sa.INTEGER(), nullable=True))

        if not is_sqlite:
            # Drop the new FK if it exists
            try:
                batch_op.drop_constraint('fk_tasks_created_by_users', type_='foreignkey')
            except Exception as e:
                 print(f"Could not drop FK constraint fk_tasks_created_by_users: {e}")
            # Recreate old FK if user_id exists (Again, risky if original name was different)
            # if column_exists('tasks', 'user_id'):
            #     batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])
        
        # Drop added columns if they exist
        if column_exists('tasks', 'completion_notes'):
            batch_op.drop_column('completion_notes')
        if column_exists('tasks', 'completed_date'):
            batch_op.drop_column('completed_date')
        if column_exists('tasks', 'reminder_2_hours'):
            batch_op.drop_column('reminder_2_hours')
        if column_exists('tasks', 'reminder_1_day'):
            batch_op.drop_column('reminder_1_day')
        if column_exists('tasks', 'created_by'):
            batch_op.drop_column('created_by')

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
