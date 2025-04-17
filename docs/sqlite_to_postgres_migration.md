# SQLite to PostgreSQL Migration Guide

This document outlines the steps to migrate your local SQLite database to Supabase PostgreSQL for production deployment.

## Prerequisites

- Access to your Supabase project
- PostgreSQL client (psql or pgAdmin)
- Python 3.x
- The Mobilize CRM application codebase

## Migration Steps

### 1. Prepare Your Environment

```bash
# Make sure you have the required Python packages
pip install psycopg2-binary
```

### 2. Configure Supabase PostgreSQL

1. Log into Supabase dashboard
2. Go to Project Settings > Database
3. Note your connection string and credentials:
   - Host: `db.[YOUR-PROJECT-ID].supabase.co`
   - Port: `5432`
   - Database: `postgres`
   - User: `postgres`
   - Password: (from your Supabase settings)

### 3. Create a Production Environment File

```bash
# Copy your development environment file
cp .env.development .env.production

# Edit the file to update the database connection strings
# Replace DATABASE_URL and DB_CONNECTION_STRING with:
# postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres
```

### 4. Initialize the PostgreSQL Database Schema

```bash
# Set production environment
export FLASK_APP=app.py
export FLASK_ENV=production
export $(grep -v '^#' .env.production | xargs)

# Apply migrations from scratch
flask db upgrade
```

### 5. Migrate Data from SQLite to PostgreSQL

Create a migration script (`migrate_data.py`):

```python
import os
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# SQLite connection
sqlite_conn = sqlite3.connect('instance/mobilize_crm.db')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL connection
pg_conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
pg_cursor = pg_conn.cursor()

# Function to transfer table data
def transfer_table(table_name, exclude_columns=None):
    if exclude_columns is None:
        exclude_columns = []
    
    # Get columns for this table
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in sqlite_cursor.fetchall() if col[1] not in exclude_columns]
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    
    # Fetch data from SQLite
    sqlite_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        print(f"No data in table {table_name}, skipping...")
        return
    
    # Prepare data for PostgreSQL
    pg_data = []
    for row in rows:
        row_data = []
        for i, col in enumerate(columns):
            # Handle SQLite boolean conversion
            if isinstance(row[i], int) and (col.endswith('_enabled') or col.startswith('is_') or col in ['virtuous', 'has_conflict']):
                row_data.append(bool(row[i]))
            else:
                row_data.append(row[i])
        pg_data.append(tuple(row_data))
    
    # Insert into PostgreSQL
    try:
        execute_values(
            pg_cursor, 
            f"INSERT INTO {table_name} ({columns_str}) VALUES %s ON CONFLICT DO NOTHING", 
            pg_data
        )
        pg_conn.commit()
        print(f"Transferred {len(pg_data)} rows to {table_name}")
    except Exception as e:
        pg_conn.rollback()
        print(f"Error transferring {table_name}: {e}")

# Migration order matters due to foreign key constraints
# Start with tables that don't depend on others
tables_ordered = [
    'permissions',
    'roles',
    'offices',
    'users',
    'contacts',
    'people',
    'churches',
    'pipelines',
    'pipeline_stages',
    'pipeline_contacts',
    'pipeline_stage_history',
    'tasks',
    'communications',
    'google_tokens',
    'email_templates',
    'email_signatures',
    'email_campaigns',
    'email_tracking'
]

# Transfer data for each table
for table in tables_ordered:
    transfer_table(table)

# Update sequences
for table in tables_ordered:
    try:
        pg_cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table}")
        pg_conn.commit()
    except Exception as e:
        print(f"Error updating sequence for {table}: {e}")

# Close connections
sqlite_cursor.close()
sqlite_conn.close()
pg_cursor.close()
pg_conn.close()

print("Migration completed!")
```

Run the migration script:

```bash
python migrate_data.py
```

### 6. Verify the Migration

```bash
# Connect to your Supabase PostgreSQL database
psql "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres"

# Check table data
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM contacts;
SELECT COUNT(*) FROM people;
```

### 7. Update Production Configuration

Make sure your production `.env` file is properly configured:

```
# Database Configuration
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres
DB_CONNECTION_STRING=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres

# Set to skip DB initialization since we've already set it up
SKIP_DB_INIT=True
```

### 8. Deploy the Application Using the PostgreSQL Database

Follow the deployment instructions in the `docs/deployment-guide.md` file, making sure to:

1. Set up secrets in GCP Secret Manager
2. Configure the deployment to use your Supabase PostgreSQL database
3. Deploy the application

## Troubleshooting

### Foreign Key Constraints

If you encounter foreign key constraint errors during migration:

1. Temporarily disable foreign key checks in PostgreSQL:
   ```sql
   SET session_replication_role = 'replica';
   ```

2. After migration, re-enable checks:
   ```sql
   SET session_replication_role = 'origin';
   ```

### Data Type Conversion Issues

- **Date/Time fields**: PostgreSQL is more strict about date formats, you may need to convert them
- **Boolean values**: SQLite uses 0/1, PostgreSQL uses true/false
- **TEXT vs VARCHAR**: PostgreSQL may enforce length limits that SQLite ignores

### PostgreSQL-Specific Configuration

You may need to adjust Supabase PostgreSQL settings for optimal performance:

1. Go to Supabase > Database > Configuration
2. Adjust connection pooling settings based on your application needs

## Post-Migration

After successful migration:

1. Run a comprehensive test of all application features
2. Verify that all data relationships are preserved
3. Check that all queries perform as expected
4. Set up automated backups for your Supabase database 