-- Add address column to contacts table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'contacts' AND column_name = 'address') THEN
        ALTER TABLE contacts ADD COLUMN address TEXT;
        RAISE NOTICE 'Added address column to contacts table';
    ELSE
        RAISE NOTICE 'address column already exists in contacts table';
    END IF;
END
$$;

-- Create churches table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables 
                   WHERE table_name = 'churches') THEN
        CREATE TABLE churches (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE
        );
        RAISE NOTICE 'Created churches table';
    ELSE
        RAISE NOTICE 'churches table already exists';
    END IF;
END
$$;
