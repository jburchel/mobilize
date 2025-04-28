"""Add Pipeline, PipelineStage, PipelineContact, and PipelineStageHistory models

Revision ID: pipeline_migration
Revises: 4cb401521a9e
Create Date: 2025-03-24 10:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'pipeline_migration'
down_revision = '4cb401521a9e'
branch_labels = None
depends_on = None


def upgrade():
    # Create tables only if they don't exist
    if not table_exists('pipelines'):
        op.create_table('pipelines',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('office_id', sa.Integer(), nullable=True),
            sa.Column('pipeline_type', sa.String(length=20), nullable=False, default='people'),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['office_id'], ['offices.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    if not table_exists('pipeline_stages'):
        op.create_table('pipeline_stages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('order', sa.Integer(), nullable=False),
            sa.Column('color', sa.String(length=20), default="#3498db"),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('auto_move_days', sa.Integer(), nullable=True),
            sa.Column('auto_reminder', sa.Boolean(), default=False),
            sa.Column('auto_task_template', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    if not table_exists('pipeline_contacts'):
        op.create_table('pipeline_contacts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('contact_id', sa.Integer(), nullable=False),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.Column('current_stage_id', sa.Integer(), nullable=False),
            sa.Column('entered_at', sa.DateTime(), nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ),
            sa.ForeignKeyConstraint(['pipeline_id'], ['pipelines.id'], ),
            sa.ForeignKeyConstraint(['current_stage_id'], ['pipeline_stages.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    
    if not table_exists('pipeline_stage_history'):
        op.create_table('pipeline_stage_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('pipeline_contact_id', sa.Integer(), nullable=False),
            sa.Column('from_stage_id', sa.Integer(), nullable=True),
            sa.Column('to_stage_id', sa.Integer(), nullable=False),
            sa.Column('moved_at', sa.DateTime(), nullable=True),
            sa.Column('moved_by_user_id', sa.Integer(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('is_automated', sa.Boolean(), default=False),
            sa.ForeignKeyConstraint(['pipeline_contact_id'], ['pipeline_contacts.id'], ),
            sa.ForeignKeyConstraint(['from_stage_id'], ['pipeline_stages.id'], ),
            sa.ForeignKeyConstraint(['to_stage_id'], ['pipeline_stages.id'], ),
            sa.ForeignKeyConstraint(['moved_by_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    # Drop tables only if they exist
    if table_exists('pipeline_stage_history'):
        op.drop_table('pipeline_stage_history')
    if table_exists('pipeline_contacts'):
        op.drop_table('pipeline_contacts')
    if table_exists('pipeline_stages'):
        op.drop_table('pipeline_stages')
    if table_exists('pipelines'):
        op.drop_table('pipelines')

# Helper function to check if table exists
def table_exists(table_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names() 