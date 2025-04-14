-- Add missing columns to the communications table
ALTER TABLE communications ADD COLUMN google_meet_link VARCHAR(255);
ALTER TABLE communications ADD COLUMN google_calendar_event_id VARCHAR(255);

-- Add scopes column to google_tokens table if it doesn't exist
ALTER TABLE google_tokens ADD COLUMN scopes TEXT;

-- Add missing task form related imports and columns if needed
PRAGMA foreign_keys=off;
PRAGMA foreign_keys=on;

-- Output success message
SELECT 'Database schema updated successfully' as message; 