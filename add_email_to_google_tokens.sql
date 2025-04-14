-- Add email column to google_tokens table if it doesn't exist
ALTER TABLE google_tokens ADD COLUMN email VARCHAR(255);

-- Output success message
SELECT 'Added email column to google_tokens table' as message; 