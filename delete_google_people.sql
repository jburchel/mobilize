-- Show counts before deletion
SELECT 'Before deletion:' AS status;
SELECT COUNT(*) AS total_people FROM people;
SELECT COUNT(*) AS google_people FROM people WHERE google_contact_id IS NOT NULL;
SELECT COUNT(*) AS total_contacts FROM contacts WHERE type = 'contact';
SELECT COUNT(*) AS google_contacts FROM contacts WHERE type = 'contact' AND google_contact_id IS NOT NULL;

-- Show people with Google contact IDs
SELECT id, first_name, last_name, google_contact_id 
FROM people 
WHERE google_contact_id IS NOT NULL
ORDER BY id;

-- Delete people with Google contact IDs (commented out for safety - uncomment to execute)
-- DELETE FROM people WHERE google_contact_id IS NOT NULL;

-- Show counts after deletion
SELECT 'After running the above delete command (if uncommented):' AS status;
SELECT COUNT(*) AS total_people FROM people;
SELECT COUNT(*) AS google_people FROM people WHERE google_contact_id IS NOT NULL; 