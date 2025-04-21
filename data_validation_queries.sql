-- Data Validation Queries for Mobilize CRM
-- Run these queries to verify data integrity after migration

-- 1. Count records in major tables
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'people', COUNT(*) FROM people
UNION ALL
SELECT 'contacts', COUNT(*) FROM contacts
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'communications', COUNT(*) FROM communications
UNION ALL
SELECT 'offices', COUNT(*) FROM offices
UNION ALL
SELECT 'pipeline_stages', COUNT(*) FROM pipeline_stages
ORDER BY table_name;

-- 2. Check for orphaned records (records with foreign keys to non-existent parent records)
-- Check people without valid office
SELECT COUNT(*) as orphaned_people_count FROM people p 
WHERE p.office_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM offices o WHERE o.id = p.office_id);

-- Check tasks without valid assignee
SELECT COUNT(*) as orphaned_tasks_count FROM tasks t
WHERE t.assignee_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM users u WHERE u.id = t.assignee_id);

-- Check communications without valid contact
SELECT COUNT(*) as orphaned_communications_count FROM communications c
WHERE c.contact_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM contacts co WHERE co.id = c.contact_id);

-- 3. Check for data consistency
-- Verify all contacts have people records
SELECT COUNT(*) as contacts_without_person FROM contacts c
WHERE NOT EXISTS (SELECT 1 FROM people p WHERE p.id = c.person_id);

-- Verify pipeline stage progression is consistent
SELECT COUNT(*) as invalid_stage_history FROM pipeline_stage_history psh
WHERE psh.from_stage_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM pipeline_stages ps WHERE ps.id = psh.from_stage_id)
OR psh.to_stage_id IS NOT NULL 
AND NOT EXISTS (SELECT 1 FROM pipeline_stages ps WHERE ps.id = psh.to_stage_id);

-- 4. Check for NULL values in required fields
SELECT 'users' as table_name, COUNT(*) as null_count FROM users WHERE email IS NULL
UNION ALL
SELECT 'people', COUNT(*) FROM people WHERE first_name IS NULL OR last_name IS NULL
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks WHERE title IS NULL
UNION ALL
SELECT 'offices', COUNT(*) FROM offices WHERE name IS NULL
ORDER BY table_name;

-- 5. Check for duplicate records
-- Check for duplicate users by email
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;

-- Check for duplicate people by name and email
SELECT first_name, last_name, email, COUNT(*) 
FROM people 
WHERE email IS NOT NULL 
GROUP BY first_name, last_name, email 
HAVING COUNT(*) > 1;

-- 6. Verify date consistency
-- Check for tasks with due dates before creation dates
SELECT COUNT(*) as invalid_task_dates FROM tasks 
WHERE due_date < date_created;

-- Check for communications with dates in the future
SELECT COUNT(*) as future_communications FROM communications 
WHERE date > CURRENT_TIMESTAMP;

-- 7. Check referential integrity of Google integrations
-- Verify Google Contact mappings are valid
SELECT COUNT(*) as invalid_google_contacts FROM contacts
WHERE google_contact_id IS NOT NULL 
AND last_synced_at IS NULL;

-- 8. Summary of validation results
-- This will be run manually and compared with expected values 