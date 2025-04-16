-- Count before deletion
SELECT COUNT(*) AS total_contacts FROM contacts;
SELECT COUNT(*) AS google_contacts FROM contacts WHERE type = 'contact' AND google_contact_id IS NOT NULL;

-- Delete Google-synced contacts that aren't associated with people or churches
DELETE FROM contacts 
WHERE type = 'contact' 
AND google_contact_id IS NOT NULL;

-- Count after deletion
SELECT COUNT(*) AS remaining_contacts FROM contacts; 