"""Fix user_id type mismatch

Revision ID: fix_user_id_type_mismatch
Revises: 
Create Date: 2025-06-02

This migration adds a database function to handle type conversion between string and integer user_ids
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'fix_user_id_type_mismatch'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create a function to safely convert between string and integer user IDs
    op.execute("""
    CREATE OR REPLACE FUNCTION match_user_id(input_id ANYELEMENT, target_id ANYELEMENT) 
    RETURNS BOOLEAN AS $$
    BEGIN
        -- Try direct comparison first
        IF input_id = target_id THEN
            RETURN TRUE;
        END IF;
        
        -- Try string conversion if types don't match
        BEGIN
            IF input_id::TEXT = target_id::TEXT THEN
                RETURN TRUE;
            END IF;
        EXCEPTION WHEN OTHERS THEN
            RETURN FALSE;
        END;
        
        RETURN FALSE;
    END;
    $$ LANGUAGE plpgsql;
    """)


def downgrade():
    # Drop the function if we need to downgrade
    op.execute("DROP FUNCTION IF EXISTS match_user_id(ANYELEMENT, ANYELEMENT);")
