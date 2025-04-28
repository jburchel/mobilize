-- Add missing columns to people table
ALTER TABLE people ADD COLUMN date_of_birth DATE;
ALTER TABLE people ADD COLUMN tags TEXT; 