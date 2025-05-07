-- Adding owner_id to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'owner_id') THEN
                    ALTER TABLE communications ADD COLUMN owner_id INTEGER;
                    RAISE NOTICE 'Added column owner_id to communications';
                END IF;
            END $$;

-- Adding office_id to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'office_id') THEN
                    ALTER TABLE communications ADD COLUMN office_id INTEGER;
                    RAISE NOTICE 'Added column office_id to communications';
                END IF;
            END $$;

-- Adding updated_at to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'updated_at') THEN
                    ALTER TABLE communications ADD COLUMN updated_at DATE;
                    RAISE NOTICE 'Added column updated_at to communications';
                END IF;
            END $$;

-- Adding google_calendar_event_id to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'google_calendar_event_id') THEN
                    ALTER TABLE communications ADD COLUMN google_calendar_event_id VARCHAR;
                    RAISE NOTICE 'Added column google_calendar_event_id to communications';
                END IF;
            END $$;

-- Adding created_at to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'created_at') THEN
                    ALTER TABLE communications ADD COLUMN created_at DATE;
                    RAISE NOTICE 'Added column created_at to communications';
                END IF;
            END $$;

-- Adding google_meet_link to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'google_meet_link') THEN
                    ALTER TABLE communications ADD COLUMN google_meet_link VARCHAR;
                    RAISE NOTICE 'Added column google_meet_link to communications';
                END IF;
            END $$;

-- Adding date to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'date') THEN
                    ALTER TABLE communications ADD COLUMN date DATE;
                    RAISE NOTICE 'Added column date to communications';
                END IF;
            END $$;

-- Adding direction to communications
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'communications' AND column_name = 'direction') THEN
                    ALTER TABLE communications ADD COLUMN direction VARCHAR(50);
                    RAISE NOTICE 'Added column direction to communications';
                END IF;
            END $$;

-- Adding email to google_tokens
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'google_tokens' AND column_name = 'email') THEN
                    ALTER TABLE google_tokens ADD COLUMN email VARCHAR;
                    RAISE NOTICE 'Added column email to google_tokens';
                END IF;
            END $$;

-- Adding scopes to google_tokens
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'google_tokens' AND column_name = 'scopes') THEN
                    ALTER TABLE google_tokens ADD COLUMN scopes TEXT;
                    RAISE NOTICE 'Added column scopes to google_tokens';
                END IF;
            END $$;

-- Adding occupation to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'occupation') THEN
                    ALTER TABLE people ADD COLUMN occupation VARCHAR(100);
                    RAISE NOTICE 'Added column occupation to people';
                END IF;
            END $$;

-- Adding pipeline_status to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'pipeline_status') THEN
                    ALTER TABLE people ADD COLUMN pipeline_status VARCHAR(50);
                    RAISE NOTICE 'Added column pipeline_status to people';
                END IF;
            END $$;

-- Adding last_contact to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'last_contact') THEN
                    ALTER TABLE people ADD COLUMN last_contact DATE;
                    RAISE NOTICE 'Added column last_contact to people';
                END IF;
            END $$;

-- Adding last_name to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'last_name') THEN
                    ALTER TABLE people ADD COLUMN last_name VARCHAR(100);
                    RAISE NOTICE 'Added column last_name to people';
                END IF;
            END $$;

-- Adding website to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'website') THEN
                    ALTER TABLE people ADD COLUMN website VARCHAR(200);
                    RAISE NOTICE 'Added column website to people';
                END IF;
            END $$;

-- Adding languages to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'languages') THEN
                    ALTER TABLE people ADD COLUMN languages TEXT;
                    RAISE NOTICE 'Added column languages to people';
                END IF;
            END $$;

-- Adding birthday to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'birthday') THEN
                    ALTER TABLE people ADD COLUMN birthday DATE;
                    RAISE NOTICE 'Added column birthday to people';
                END IF;
            END $$;

-- Adding is_primary_contact to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'is_primary_contact') THEN
                    ALTER TABLE people ADD COLUMN is_primary_contact BOOLEAN;
                    RAISE NOTICE 'Added column is_primary_contact to people';
                END IF;
            END $$;

-- Adding twitter to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'twitter') THEN
                    ALTER TABLE people ADD COLUMN twitter VARCHAR(100);
                    RAISE NOTICE 'Added column twitter to people';
                END IF;
            END $$;

-- Adding anniversary to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'anniversary') THEN
                    ALTER TABLE people ADD COLUMN anniversary DATE;
                    RAISE NOTICE 'Added column anniversary to people';
                END IF;
            END $$;

-- Adding first_name to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'first_name') THEN
                    ALTER TABLE people ADD COLUMN first_name VARCHAR(100);
                    RAISE NOTICE 'Added column first_name to people';
                END IF;
            END $$;

-- Adding tags to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'tags') THEN
                    ALTER TABLE people ADD COLUMN tags TEXT;
                    RAISE NOTICE 'Added column tags to people';
                END IF;
            END $$;

-- Adding facebook to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'facebook') THEN
                    ALTER TABLE people ADD COLUMN facebook VARCHAR(100);
                    RAISE NOTICE 'Added column facebook to people';
                END IF;
            END $$;

-- Adding next_contact to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'next_contact') THEN
                    ALTER TABLE people ADD COLUMN next_contact DATE;
                    RAISE NOTICE 'Added column next_contact to people';
                END IF;
            END $$;

-- Adding linkedin to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'linkedin') THEN
                    ALTER TABLE people ADD COLUMN linkedin VARCHAR(100);
                    RAISE NOTICE 'Added column linkedin to people';
                END IF;
            END $$;

-- Adding google_contact_id to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'google_contact_id') THEN
                    ALTER TABLE people ADD COLUMN google_contact_id VARCHAR(255);
                    RAISE NOTICE 'Added column google_contact_id to people';
                END IF;
            END $$;

-- Adding employer to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'employer') THEN
                    ALTER TABLE people ADD COLUMN employer VARCHAR(100);
                    RAISE NOTICE 'Added column employer to people';
                END IF;
            END $$;

-- Adding status to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'status') THEN
                    ALTER TABLE people ADD COLUMN status VARCHAR(50);
                    RAISE NOTICE 'Added column status to people';
                END IF;
            END $$;

-- Adding last_synced_at to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'last_synced_at') THEN
                    ALTER TABLE people ADD COLUMN last_synced_at DATE;
                    RAISE NOTICE 'Added column last_synced_at to people';
                END IF;
            END $$;

-- Adding instagram to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'instagram') THEN
                    ALTER TABLE people ADD COLUMN instagram VARCHAR(100);
                    RAISE NOTICE 'Added column instagram to people';
                END IF;
            END $$;

-- Adding skills to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'skills') THEN
                    ALTER TABLE people ADD COLUMN skills TEXT;
                    RAISE NOTICE 'Added column skills to people';
                END IF;
            END $$;

-- Adding interests to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'interests') THEN
                    ALTER TABLE people ADD COLUMN interests TEXT;
                    RAISE NOTICE 'Added column interests to people';
                END IF;
            END $$;

-- Adding pipeline_stage to people
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'people' AND column_name = 'pipeline_stage') THEN
                    ALTER TABLE people ADD COLUMN pipeline_stage VARCHAR(50);
                    RAISE NOTICE 'Added column pipeline_stage to people';
                END IF;
            END $$;

-- Adding assigned_at to user_offices
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'user_offices' AND column_name = 'assigned_at') THEN
                    ALTER TABLE user_offices ADD COLUMN assigned_at DATE;
                    RAISE NOTICE 'Added column assigned_at to user_offices';
                END IF;
            END $$;

-- Adding updated_at to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'updated_at') THEN
                    ALTER TABLE contacts ADD COLUMN updated_at DATE;
                    RAISE NOTICE 'Added column updated_at to contacts';
                END IF;
            END $$;

-- Adding last_synced_at to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'last_synced_at') THEN
                    ALTER TABLE contacts ADD COLUMN last_synced_at DATE;
                    RAISE NOTICE 'Added column last_synced_at to contacts';
                END IF;
            END $$;

-- Adding created_at to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'created_at') THEN
                    ALTER TABLE contacts ADD COLUMN created_at DATE;
                    RAISE NOTICE 'Added column created_at to contacts';
                END IF;
            END $$;

-- Adding conflict_data to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'conflict_data') THEN
                    ALTER TABLE contacts ADD COLUMN conflict_data JSONB;
                    RAISE NOTICE 'Added column conflict_data to contacts';
                END IF;
            END $$;

-- Adding google_contact_id to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'google_contact_id') THEN
                    ALTER TABLE contacts ADD COLUMN google_contact_id VARCHAR(255);
                    RAISE NOTICE 'Added column google_contact_id to contacts';
                END IF;
            END $$;

-- Adding has_conflict to contacts
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'contacts' AND column_name = 'has_conflict') THEN
                    ALTER TABLE contacts ADD COLUMN has_conflict BOOLEAN;
                    RAISE NOTICE 'Added column has_conflict to contacts';
                END IF;
            END $$;