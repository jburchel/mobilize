import os
import psycopg2
from dotenv import load_dotenv

# Load production environment variables
load_dotenv('.env.production')

def get_db_connection():
    """Create a connection to the Supabase database."""
    conn_string = os.getenv('DB_CONNECTION_STRING')
    try:
        conn = psycopg2.connect(conn_string)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def create_tables(conn):
    """Create all tables in the database."""
    with conn.cursor() as cur:
        # Create contacts table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id SERIAL PRIMARY KEY,
                type VARCHAR(20) NOT NULL CHECK (type IN ('person', 'church')),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                office_id INTEGER,
                email VARCHAR(255),
                phone VARCHAR(20),
                address_street VARCHAR(255),
                address_city VARCHAR(100),
                address_state VARCHAR(50),
                address_zip VARCHAR(20),
                address_country VARCHAR(100),
                notes TEXT,
                pipeline_stage VARCHAR(50),
                priority VARCHAR(20),
                status VARCHAR(20) DEFAULT 'active',
                last_contact_date TIMESTAMP,
                next_contact_date TIMESTAMP,
                tags TEXT[],
                custom_fields JSONB
            )
        """)

        # Create users table first since it's referenced by other tables
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                firebase_uid VARCHAR(128) NOT NULL UNIQUE,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                role VARCHAR(20) NOT NULL DEFAULT 'standard_user',
                preferences JSONB,
                email_signature TEXT,
                notification_settings JSONB,
                theme_preferences JSONB,
                google_refresh_token TEXT,
                profile_picture_url VARCHAR(255)
            )
        """)

        # Create offices table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS offices (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                location VARCHAR(255),
                timezone VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                contact_email VARCHAR(255),
                contact_phone VARCHAR(20),
                address JSONB,
                settings JSONB
            )
        """)

        # Create people table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS people (
                id INTEGER PRIMARY KEY REFERENCES contacts(id),
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                title VARCHAR(50),
                preferred_name VARCHAR(100),
                preferred_contact_method VARCHAR(20),
                birth_date DATE,
                marital_status VARCHAR(20),
                spouse_first_name VARCHAR(100),
                spouse_last_name VARCHAR(100),
                home_country VARCHAR(100),
                languages TEXT[],
                profession VARCHAR(100),
                organization VARCHAR(255),
                church_role VARCHAR(100),
                primary_church_id INTEGER,
                linkedin_url VARCHAR(255),
                facebook_url VARCHAR(255),
                twitter_url VARCHAR(255),
                instagram_url VARCHAR(255),
                google_contact_id VARCHAR(255),
                CONSTRAINT fk_person_contact FOREIGN KEY (id) 
                    REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)

        # Create churches table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS churches (
                id INTEGER PRIMARY KEY REFERENCES contacts(id),
                name VARCHAR(255) NOT NULL,
                denomination VARCHAR(100),
                website VARCHAR(255),
                congregation_size INTEGER,
                year_founded INTEGER,
                service_times JSONB,
                pastor_name VARCHAR(200),
                pastor_email VARCHAR(255),
                pastor_phone VARCHAR(20),
                facilities TEXT[],
                ministries TEXT[],
                primary_language VARCHAR(50),
                secondary_languages TEXT[],
                CONSTRAINT fk_church_contact FOREIGN KEY (id) 
                    REFERENCES contacts(id) ON DELETE CASCADE
            )
        """)

        # Create tasks table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                priority VARCHAR(20) NOT NULL DEFAULT 'medium',
                assigned_to INTEGER REFERENCES users(id),
                created_by INTEGER NOT NULL REFERENCES users(id),
                contact_id INTEGER REFERENCES contacts(id),
                category VARCHAR(50),
                google_calendar_event_id VARCHAR(255),
                reminder_sent BOOLEAN DEFAULT FALSE,
                recurring_pattern JSONB,
                completion_notes TEXT
            )
        """)

        # Create communications table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS communications (
                id SERIAL PRIMARY KEY,
                type VARCHAR(20) NOT NULL,
                subject VARCHAR(255),
                content TEXT,
                sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                recipient_contact_id INTEGER REFERENCES contacts(id),
                status VARCHAR(20) NOT NULL DEFAULT 'sent',
                gmail_thread_id VARCHAR(255),
                gmail_message_id VARCHAR(255),
                attachments JSONB,
                metadata JSONB,
                template_used INTEGER,
                read_status BOOLEAN DEFAULT FALSE,
                read_timestamp TIMESTAMP
            )
        """)

        # Create email_templates table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS email_templates (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                created_by INTEGER REFERENCES users(id),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                category VARCHAR(50),
                variables JSONB
            )
        """)

        # Create user_offices junction table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_offices (
                user_id INTEGER REFERENCES users(id),
                office_id INTEGER REFERENCES offices(id),
                role VARCHAR(20) NOT NULL,
                assigned_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, office_id)
            )
        """)

        # Create google_tokens table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS google_tokens (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                access_token TEXT NOT NULL,
                refresh_token TEXT,
                token_type VARCHAR(50),
                expires_at TIMESTAMP NOT NULL,
                scopes TEXT[],
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create activity_logs table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                action_type VARCHAR(50) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                entity_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                details JSONB,
                ip_address VARCHAR(45)
            )
        """)

        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_pipeline ON contacts(pipeline_stage)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_contacts_office ON contacts(office_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_people_name ON people(last_name, first_name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_churches_name ON churches(name)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_communications_contact ON communications(recipient_contact_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_communications_gmail ON communications(gmail_message_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_firebase ON users(firebase_uid)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_offices ON user_offices(user_id, office_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_google_tokens_user ON google_tokens(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_entity ON activity_logs(entity_type, entity_id)")

def main():
    """Main function to run the migration."""
    try:
        conn = get_db_connection()
        create_tables(conn)
        conn.commit()
        print("Successfully created all tables and indexes in Supabase database")
    except Exception as e:
        print(f"Error during migration: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main() 