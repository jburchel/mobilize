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
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite workaround
        if not column_exists('contacts', 'user_id'):
            op.add_column('contacts', sa.Column('user_id', sa.Integer(), nullable=True)) # Add nullable
            # No default update needed as user_id is nullable
        # Cannot add FK in SQLite alter
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('contacts', schema=None) as batch_op:
            if not column_exists('contacts', 'user_id'): # Check for idempotency
                batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
            # Add FK constraint
            batch_op.create_foreign_key('fk_contacts_user_id_users', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite simple drop column
        try:
            if column_exists('contacts', 'user_id'):
                 op.drop_column('contacts', 'user_id')
        except Exception as e:
            print(f"Could not drop user_id from contacts (SQLite): {e}")
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('contacts', schema=None) as batch_op:
            try:
                batch_op.drop_constraint('fk_contacts_user_id_users', type_='foreignkey')
            except Exception as e:
                print(f"Could not drop FK constraint fk_contacts_user_id_users: {e}")
            if column_exists('contacts', 'user_id'):
                batch_op.drop_column('user_id')
    # ### end Alembic commands ###

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
