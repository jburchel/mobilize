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
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite workaround: Add column directly if it doesn't exist
        if not column_exists('users', 'person_id'):
            op.add_column('users', sa.Column('person_id', sa.Integer(), nullable=True))
        # Cannot add FK constraint in SQLite alter
    else:
        # Use batch mode for other databases
        with op.batch_alter_table('users', schema=None) as batch_op:
            if not column_exists('users', 'person_id'): # Check for idempotency
                batch_op.add_column(sa.Column('person_id', sa.Integer(), nullable=True))
            # Add FK constraint
            batch_op.create_foreign_key('fk_users_person_id', 'people', ['person_id'], ['id'])


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite workaround: Drop column directly if it exists
        try:
             if column_exists('users', 'person_id'):
                 op.drop_column('users', 'person_id')
        except Exception as e:
            print(f"Could not drop person_id from users (SQLite): {e}")
    else:
        # Use batch mode for other databases
        with op.batch_alter_table('users', schema=None) as batch_op:
            try:
                batch_op.drop_constraint('fk_users_person_id', type_='foreignkey')
            except Exception as e:
                 print(f"Could not drop FK constraint fk_users_person_id: {e}")
            if column_exists('users', 'person_id'):
                batch_op.drop_column('person_id')

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
