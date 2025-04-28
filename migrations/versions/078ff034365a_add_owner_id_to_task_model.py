"""Add owner_id to Task model

Revision ID: 078ff034365a
Revises: 1593af608f53
Create Date: 2025-03-20 10:54:40.547457

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '078ff034365a'
down_revision = '1593af608f53'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite workaround - avoid batch mode and complex alters
        if not column_exists('tasks', 'owner_id'):
            op.add_column('tasks', sa.Column('owner_id', sa.Integer(), nullable=True)) # Add nullable
            op.execute('UPDATE tasks SET owner_id = 1 WHERE owner_id IS NULL') # Set default, adjust as needed
            # Cannot easily make non-nullable or add FK in SQLite alter
            # op.alter_column('tasks', 'owner_id', nullable=False)
        else:
            # If it exists, try ensuring a default value is set if needed
            op.execute('UPDATE tasks SET owner_id = 1 WHERE owner_id IS NULL') # Adjust default as needed
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('tasks', schema=None) as batch_op:
            if not column_exists('tasks', 'owner_id'): # Check for idempotency
                batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True)) # Add nullable first
                batch_op.execute('UPDATE tasks SET owner_id = 1 WHERE owner_id IS NULL') # Set default
                batch_op.alter_column('owner_id', nullable=False)
            else:
                # Ensure not nullable if it already exists
                 batch_op.alter_column('owner_id', nullable=False)
            # Add FK constraint
            batch_op.create_foreign_key('fk_tasks_owner_id_users', 'users', ['owner_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite simple drop column
        try:
            if column_exists('tasks', 'owner_id'):
                op.drop_column('tasks', 'owner_id')
        except Exception as e:
             print(f"Could not drop owner_id from tasks (SQLite): {e}")
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('tasks', schema=None) as batch_op:
            try:
                batch_op.drop_constraint('fk_tasks_owner_id_users', type_='foreignkey')
            except Exception as e:
                # May fail if constraint doesn't exist, ignore
                print(f"Could not drop FK constraint fk_tasks_owner_id_users: {e}")
            if column_exists('tasks', 'owner_id'):
                batch_op.drop_column('owner_id')
    # ### end Alembic commands ###

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
