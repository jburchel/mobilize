-- SQLite data export for PostgreSQL import
-- Generated: 2025-05-01T09:41:07.692642
-- Tables: roles, users, churches, offices, people, contacts, tasks, communications, pipeline_stages, pipeline_stage_history, role_permissions

BEGIN;

-- Data for table users (2 rows)
INSERT INTO users (id, username, email, password_hash, firebase_uid, first_name, last_name, phone, profile_image, job_title, department, is_active, first_login, role, role_id, last_login, preferences, notification_settings, google_refresh_token, google_calendar_sync, google_meet_enabled, email_sync_contacts_only, office_id, person_id, created_at, updated_at) VALUES (1, 'j.burchel', 'j.burchel@crossoverglobal.net', NULL, 'google-oauth-7b5296ee-a603-4401-8848-a50ae9c19cb9', 'Jim', 'Burchel', NULL, 'https://lh3.googleusercontent.com/a/ACg8ocJqFwDIMGPJiUu7CYGL1zCArCPbUqvqxf-BGPhpSf7RfufjAbQ=s96-c', NULL, NULL, 1, 0, 'standard_user', NULL, '2025-04-29 17:24:12.249998', NULL, '{"email_notifications": true, "task_reminders": true, "task_assignments": true, "system_announcements": true}', NULL, 1, 1, 1, 1, NULL, '2025-04-29 17:24:11.978882', '2025-04-29 17:27:39.167049');
INSERT INTO users (id, username, email, password_hash, firebase_uid, first_name, last_name, phone, profile_image, job_title, department, is_active, first_login, role, role_id, last_login, preferences, notification_settings, google_refresh_token, google_calendar_sync, google_meet_enabled, email_sync_contacts_only, office_id, person_id, created_at, updated_at) VALUES (2, 'testuser', 'test@example.com', NULL, 'dev-test-user', 'Test', 'User', NULL, NULL, NULL, NULL, 1, 0, 'super_admin', NULL, NULL, NULL, '{"email_notifications": true, "task_reminders": true, "task_assignments": true, "system_announcements": true}', NULL, 1, 1, 1, 1, NULL, '2025-04-29 17:28:08.192959', '2025-04-29 17:28:12.506315');
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users), true);

COMMIT;
