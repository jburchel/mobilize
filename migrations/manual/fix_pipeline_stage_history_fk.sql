-- Fix the foreign key constraint on pipeline_stage_history table
-- This adds ON DELETE CASCADE to the constraint

-- First, drop the existing constraint
ALTER TABLE pipeline_stage_history DROP CONSTRAINT IF EXISTS pipeline_stage_history_pipeline_contact_id_fkey;

-- Then recreate it with ON DELETE CASCADE
ALTER TABLE pipeline_stage_history ADD CONSTRAINT pipeline_stage_history_pipeline_contact_id_fkey
    FOREIGN KEY (pipeline_contact_id) REFERENCES pipeline_contacts(id) ON DELETE CASCADE;
