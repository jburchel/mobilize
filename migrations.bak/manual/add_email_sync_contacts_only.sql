-- Add email_sync_contacts_only column to users table
ALTER TABLE users ADD COLUMN email_sync_contacts_only BOOLEAN DEFAULT 0;

-- Update existing users to have the default value
UPDATE users SET email_sync_contacts_only = 0 WHERE email_sync_contacts_only IS NULL; 