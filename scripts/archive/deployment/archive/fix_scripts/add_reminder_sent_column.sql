-- Add reminder_sent column to tasks table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'tasks' AND column_name = 'reminder_sent') THEN
        ALTER TABLE tasks ADD COLUMN reminder_sent BOOLEAN DEFAULT FALSE;
        RAISE NOTICE 'Added reminder_sent column to tasks table';
    ELSE
        RAISE NOTICE 'reminder_sent column already exists in tasks table';
    END IF;
END
$$;
