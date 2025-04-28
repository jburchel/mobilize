"""Add role_id to users and create roles and role_permissions tables

Revision ID: add_roles_perms
Revises: eeb2b80b5f20
Create Date: 2025-04-15 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_roles_perms'
down_revision = 'eeb2b80b5f20'
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table if it doesn't exist
    if not table_exists('roles'):
        op.create_table('roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name')
        )
        # Insert default roles only if table was just created
        op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('super_admin', 'Super Administrator with full access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
        op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('office_admin', 'Office Administrator with access to manage office resources', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
        op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('standard_user', 'Standard user with basic access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
        op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('limited_user', 'Limited user with restricted access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")

    # Create role_permissions table if it doesn't exist
    if not table_exists('role_permissions'):
        op.create_table('role_permissions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('role_id', sa.Integer(), nullable=False),
            sa.Column('permission_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ),
            sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
        )
    
    # Add role_id column to users table if it doesn't exist
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    if not column_exists('users', 'role_id'):
        if is_sqlite:
            op.add_column('users', sa.Column('role_id', sa.Integer(), nullable=True))
        else:
             with op.batch_alter_table('users', schema=None) as batch_op:
                batch_op.add_column(sa.Column('role_id', sa.Integer(), nullable=True))
                # Add FK only if column was added and not SQLite
                batch_op.create_foreign_key('fk_users_role_id_roles', 'roles', ['role_id'], ['id'])
    elif not is_sqlite:
         # If column exists, ensure FK exists for non-SQLite
         with op.batch_alter_table('users', schema=None) as batch_op:
             try:
                 batch_op.create_foreign_key('fk_users_role_id_roles', 'roles', ['role_id'], ['id'])
             except Exception as e:
                 print(f"Could not create FK fk_users_role_id_roles (might exist): {e}")


def downgrade():
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    # Remove role_id from users table if it exists
    if column_exists('users', 'role_id'):
        if is_sqlite:
             try:
                 # Need batch for SQLite drop
                 with op.batch_alter_table('users', schema=None) as batch_op:
                     batch_op.drop_column('role_id')
             except Exception as e:
                 print(f"Could not drop role_id from users (SQLite): {e}")
        else:
             with op.batch_alter_table('users', schema=None) as batch_op:
                try:
                    batch_op.drop_constraint('fk_users_role_id_roles', type_='foreignkey')
                except Exception as e:
                    print(f"Could not drop FK constraint fk_users_role_id_roles: {e}")
                batch_op.drop_column('role_id')
    
    # Drop role_permissions table if it exists
    if table_exists('role_permissions'):
        op.drop_table('role_permissions')
    
    # Drop roles table if it exists
    if table_exists('roles'):
        op.drop_table('roles')

# Helper function to check if table exists
def table_exists(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns 