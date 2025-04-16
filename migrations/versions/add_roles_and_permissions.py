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
    # Create roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create role_permissions table
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
    
    # Add role_id column to users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_users_role_id_roles', 'roles', ['role_id'], ['id'])
    
    # Insert default roles
    op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('super_admin', 'Super Administrator with full access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('office_admin', 'Office Administrator with access to manage office resources', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('standard_user', 'Standard user with basic access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")
    op.execute("INSERT INTO roles (name, description, created_at, updated_at) VALUES ('limited_user', 'Limited user with restricted access', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)")


def downgrade():
    # Remove role_id from users table
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('fk_users_role_id_roles', type_='foreignkey')
        batch_op.drop_column('role_id')
    
    # Drop role_permissions table
    op.drop_table('role_permissions')
    
    # Drop roles table
    op.drop_table('roles') 