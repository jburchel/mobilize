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
    # Add is_main_pipeline column with default value of False
    op.add_column('pipelines', sa.Column('is_main_pipeline', sa.Boolean(), 
                                        nullable=False, server_default='0'))
    
    # Add parent_pipeline_stage column as nullable string
    op.add_column('pipelines', sa.Column('parent_pipeline_stage', sa.String(50), 
                                        nullable=True))


def downgrade():
    """Remove the added columns if needed."""
    op.drop_column('pipelines', 'parent_pipeline_stage')
    op.drop_column('pipelines', 'is_main_pipeline') 