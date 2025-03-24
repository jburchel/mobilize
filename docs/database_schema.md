# Database Schema

## Core Models

### Office
```sql
CREATE TABLE office (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    settings JSON,  -- Store office-specific settings
    is_active BOOLEAN DEFAULT TRUE
);
```

### User
```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    office_id INTEGER REFERENCES office(id),
    role VARCHAR(50) NOT NULL,  -- 'super_admin', 'office_admin', 'user'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    settings JSON  -- Store user preferences
);
```

### Person (Contact)
```sql
CREATE TABLE person (
    id INTEGER PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    owner_id INTEGER NOT NULL REFERENCES user(id),  -- User who "owns" this contact
    office_id INTEGER NOT NULL REFERENCES office(id),
    pipeline_stage VARCHAR(50),
    priority VARCHAR(50),
    date_of_birth DATE,
    profile_image VARCHAR(255),
    tags TEXT,  -- Comma-separated tags
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Church
```sql
CREATE TABLE church (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    office_id INTEGER NOT NULL REFERENCES office(id),  -- Church belongs to an office
    owner_id INTEGER NOT NULL REFERENCES user(id),     -- User who "owns" this church
    address TEXT,
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Church-Person Association
```sql
-- Create enum for common church roles
CREATE TYPE church_role AS ENUM (
    -- Leadership
    'senior_pastor', 'associate_pastor', 'youth_pastor', 'worship_pastor',
    'elder', 'deacon', 'board_member', 'ministry_leader',
    
    -- Staff
    'administrative_staff', 'secretary', 'treasurer', 'bookkeeper',
    'facilities_manager', 'technical_director', 'communications_director',
    
    -- Volunteer
    'sunday_school_teacher', 'small_group_leader', 'worship_team_member',
    'usher', 'greeter', 'nursery_worker', 'youth_group_leader',
    'media_team_member', 'outreach_coordinator',
    
    -- Member Status
    'member', 'regular_attendee', 'visitor', 'prospect', 'former_member',
    
    -- Other
    'other'  -- For custom roles not in the predefined list
);

CREATE TABLE church_person (
    church_id INTEGER REFERENCES church(id),
    person_id INTEGER REFERENCES person(id),
    role church_role,  -- Optional: role can be NULL if unknown or not yet determined
    role_details VARCHAR(100),  -- For additional details when role is 'other'
    start_date DATE,           -- When they started this role
    end_date DATE,             -- Optional: when they ended this role (if applicable)
    is_active BOOLEAN DEFAULT TRUE,  -- Whether this role is current
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (church_id, person_id)
);

-- Index for role queries
CREATE INDEX idx_church_person_role ON church_person(role);
CREATE INDEX idx_church_person_active ON church_person(is_active);
```

### Task
```sql
CREATE TABLE task (
    id INTEGER PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date DATE,
    priority VARCHAR(50),
    status VARCHAR(50),
    owner_id INTEGER NOT NULL REFERENCES user(id),  -- Task creator
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Task Participants
```sql
CREATE TABLE task_participant (
    task_id INTEGER REFERENCES task(id),
    user_id INTEGER REFERENCES user(id),
    role VARCHAR(50) DEFAULT 'participant',  -- 'owner', 'participant'
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (task_id, user_id)
);
```

### Communication Types
```sql
CREATE TYPE communication_type AS ENUM (
    'email',
    'phone_call',
    'text_message',
    'in_person_meeting',
    'video_meeting'
);
```

### Communication
```sql
CREATE TABLE communication (
    id INTEGER PRIMARY KEY,
    type communication_type NOT NULL,
    notes TEXT,
    creator_id INTEGER NOT NULL REFERENCES user(id),
    office_id INTEGER NOT NULL REFERENCES office(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,  -- For scheduled communications
    completed_at TIMESTAMP,  -- When the communication actually occurred
    duration_minutes INTEGER, -- Duration of calls/meetings
    location TEXT,          -- For in-person meetings
    status VARCHAR(50) NOT NULL DEFAULT 'completed',  -- 'scheduled', 'completed', 'cancelled'
    
    -- Integration References
    gmail_thread_id VARCHAR(255),    -- Reference to Gmail thread
    gmail_message_id VARCHAR(255),   -- Reference to specific Gmail message
    google_meet_link VARCHAR(255),   -- Google Meet link
    google_calendar_event_id VARCHAR(255),  -- Reference to Google Calendar event
    google_doc_id VARCHAR(255),      -- Reference to associated Google Doc (meeting notes)
    
    -- Mobile Integration
    device_id VARCHAR(255),          -- For mobile app integration (texting)
    message_thread_id VARCHAR(255)   -- For tracking text message threads
);

-- Indexes for integration queries
CREATE INDEX idx_communication_gmail_thread ON communication(gmail_thread_id);
CREATE INDEX idx_communication_calendar_event ON communication(google_calendar_event_id);
CREATE INDEX idx_communication_status ON communication(status);
CREATE INDEX idx_communication_scheduled ON communication(scheduled_at);
```

### Email Integration Settings
```sql
CREATE TABLE email_integration (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    gmail_email VARCHAR(255) NOT NULL,
    oauth_refresh_token TEXT,
    oauth_access_token TEXT,
    oauth_expiry TIMESTAMP,
    sync_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, gmail_email)
);
```

### Google Workspace Integration Settings
```sql
CREATE TABLE google_workspace_integration (
    id INTEGER PRIMARY KEY,
    office_id INTEGER NOT NULL REFERENCES office(id),
    workspace_domain VARCHAR(255) NOT NULL,  -- e.g., "yourorg.com"
    calendar_sync_enabled BOOLEAN DEFAULT TRUE,
    meet_integration_enabled BOOLEAN DEFAULT TRUE,
    drive_integration_enabled BOOLEAN DEFAULT TRUE,
    oauth_settings JSON,  -- Store workspace-level OAuth configuration
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (office_id, workspace_domain)
);
```

### Mobile Device Integration
```sql
CREATE TABLE mobile_device (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    device_identifier VARCHAR(255) NOT NULL,
    device_name VARCHAR(255),
    device_type VARCHAR(50),  -- 'ios', 'android'
    phone_number VARCHAR(50),
    sms_integration_enabled BOOLEAN DEFAULT FALSE,
    push_notifications_enabled BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, device_identifier)
);

-- Index for device queries
CREATE INDEX idx_mobile_device_user ON mobile_device(user_id);
CREATE INDEX idx_mobile_device_phone ON mobile_device(phone_number);
```

### Communication Attachments
```sql
CREATE TABLE communication_attachment (
    id INTEGER PRIMARY KEY,
    communication_id INTEGER NOT NULL REFERENCES communication(id),
    file_type VARCHAR(50) NOT NULL,  -- 'document', 'image', 'other'
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    
    -- Storage references
    google_drive_file_id VARCHAR(255),  -- If stored in Google Drive
    local_file_path VARCHAR(255),       -- If stored locally
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for attachment queries
CREATE INDEX idx_communication_attachment_comm ON communication_attachment(communication_id);
```

## Key Features of the Schema

1. **Office Isolation**
   - Each office has its own set of churches
   - Users are associated with one office
   - People (contacts) belong to specific users within offices

2. **Data Ownership**
   - People are owned by specific users
   - Tasks have owners and participants
   - Communications are associated with offices for shared visibility

3. **Flexible Relationships**
   - People can be associated with multiple churches
   - Tasks can have multiple participants across offices
   - Communications can target either people or churches

4. **Audit Trail**
   - All tables include creation timestamps
   - Key tables include update timestamps
   - All relationships maintain creation timestamps

## Indexes and Constraints

Important indexes to be created:
```sql
-- User indexes
CREATE INDEX idx_user_office ON user(office_id);
CREATE INDEX idx_user_email ON user(email);

-- Person indexes
CREATE INDEX idx_person_owner ON person(owner_id);
CREATE INDEX idx_person_office ON person(office_id);

-- Church indexes
CREATE INDEX idx_church_office ON church(office_id);
CREATE INDEX idx_church_owner ON church(owner_id);
CREATE INDEX idx_church_office_owner ON church(office_id, owner_id);

-- Task indexes
CREATE INDEX idx_task_owner ON task(owner_id);
CREATE INDEX idx_task_due_date ON task(due_date);

-- Communication indexes
CREATE INDEX idx_communication_office ON communication(office_id);
CREATE INDEX idx_communication_creator ON communication(creator_id);
``` 