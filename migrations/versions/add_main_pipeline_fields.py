"""
Add main pipeline fields to Pipeline model

This migration adds two fields to the pipelines table:
1. is_main_pipeline (Boolean): Identifies whether a pipeline is a main/system pipeline
2. parent_pipeline_stage (String): The stage of the main pipeline that a custom pipeline belongs to
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_main_pipeline_fields'
down_revision = None  # Set this to the previous migration if there is one
branch_labels = None
depends_on = None


def upgrade():
    """Add main pipeline fields to pipelines table."""
    # Add columns only if they don't exist
    if not column_exists('pipelines', 'is_main_pipeline'):
        op.add_column('pipelines', sa.Column('is_main_pipeline', sa.Boolean(), 
                                            nullable=False, server_default='0'))
    
    if not column_exists('pipelines', 'parent_pipeline_stage'):
        op.add_column('pipelines', sa.Column('parent_pipeline_stage', sa.String(50), 
                                            nullable=True))


def downgrade():
    """Remove the added columns if needed."""
    # Drop columns only if they exist
    if column_exists('pipelines', 'parent_pipeline_stage'):
        op.drop_column('pipelines', 'parent_pipeline_stage')
    if column_exists('pipelines', 'is_main_pipeline'):
        op.drop_column('pipelines', 'is_main_pipeline')

# Helper function to check if column exists
def column_exists(table_name, column_name):
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns 