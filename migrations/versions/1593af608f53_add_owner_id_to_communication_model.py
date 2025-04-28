"""Add owner_id to Communication model

Revision ID: 1593af608f53
Revises: 
Create Date: 2025-03-20 10:52:44.635757

"""
from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision = '1593af608f53'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    # Use batch mode for adding/altering columns, works better with SQLite limitations
    with op.batch_alter_table('communications', schema=None) as batch_op:
        if not column_exists('communications', 'owner_id'):
            batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True)) # Add as nullable first
            # Update existing rows - adjust default value as necessary
            batch_op.execute('UPDATE communications SET owner_id = 1 WHERE owner_id IS NULL')
            # Now make non-nullable if possible within batch (often works)
            batch_op.alter_column('owner_id', nullable=False)
        else:
             # If column already exists, ensure it's not nullable
             batch_op.alter_column('owner_id', nullable=False)

    # Add Foreign Key constraint only if not SQLite
    if not is_sqlite:
        op.create_foreign_key(
            'fk_communications_owner_id_users',
            'communications', 'users', 
            ['owner_id'], ['id']
        )

    # Repeat for churches table
    with op.batch_alter_table('churches', schema=None) as batch_op:
        if not column_exists('churches', 'owner_id'):
            batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
            batch_op.execute('UPDATE churches SET owner_id = 1 WHERE owner_id IS NULL')
            batch_op.alter_column('owner_id', nullable=False)
        else:
            batch_op.alter_column('owner_id', nullable=False)

    # Add Foreign Key constraint only if not SQLite
    if not is_sqlite:
         op.create_foreign_key(
             'fk_churches_owner_id_users',
             'churches', 'users', 
             ['owner_id'], ['id']
         )
    # ### end Alembic commands ###


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'

    # Drop Foreign Key constraint only if not SQLite
    if not is_sqlite:
        op.drop_constraint('fk_churches_owner_id_users', 'churches', type_='foreignkey')
        op.drop_constraint('fk_communications_owner_id_users', 'communications', type_='foreignkey')

    # Use batch mode for dropping columns
    with op.batch_alter_table('churches', schema=None) as batch_op:
        if column_exists('churches', 'owner_id'):
            batch_op.drop_column('owner_id')

    with op.batch_alter_table('communications', schema=None) as batch_op:
        if column_exists('communications', 'owner_id'):
            batch_op.drop_column('owner_id')
    # ### end Alembic commands ###

# Helper function to check if column exists, needed for conditional logic
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns
