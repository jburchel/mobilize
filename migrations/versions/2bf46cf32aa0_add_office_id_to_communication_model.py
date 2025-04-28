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
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite workaround
        if not column_exists('communications', 'office_id'):
            op.add_column('communications', sa.Column('office_id', sa.Integer(), nullable=True)) # Add nullable
            # Set a default office_id - adjust '1' as necessary for your default office
            op.execute('UPDATE communications SET office_id = 1 WHERE office_id IS NULL') 
            # Cannot easily make non-nullable or add FK in SQLite alter
            # op.alter_column('communications', 'office_id', nullable=False)
        else:
            # If column exists, ensure default is set
            op.execute('UPDATE communications SET office_id = 1 WHERE office_id IS NULL')
            # op.alter_column('communications', 'office_id', nullable=False) # Attempt to ensure not null
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('communications', schema=None) as batch_op:
            if not column_exists('communications', 'office_id'): # Check for idempotency
                batch_op.add_column(sa.Column('office_id', sa.Integer(), nullable=True)) # Add nullable
                batch_op.execute('UPDATE communications SET office_id = 1 WHERE office_id IS NULL') # Set default
                batch_op.alter_column('office_id', nullable=False) # Make non-nullable
            else:
                batch_op.alter_column('office_id', nullable=False)
            # Add FK constraint
            batch_op.create_foreign_key('fk_communications_office_id_offices', 'offices', ['office_id'], ['id'])


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    if is_sqlite:
        # SQLite simple drop column
        try:
            if column_exists('communications', 'office_id'):
                 op.drop_column('communications', 'office_id')
        except Exception as e:
            print(f"Could not drop office_id from communications (SQLite): {e}")
    else:
        # Original batch logic for other databases
        with op.batch_alter_table('communications', schema=None) as batch_op:
            try:
                batch_op.drop_constraint('fk_communications_office_id_offices', type_='foreignkey')
            except Exception as e:
                print(f"Could not drop FK constraint fk_communications_office_id_offices: {e}")
            if column_exists('communications', 'office_id'):
                batch_op.drop_column('office_id')

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
