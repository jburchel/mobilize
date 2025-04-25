# SQLite to PostgreSQL Migration Checklist

## Prerequisites Checklist

- [x] Confirm access to Supabase project
- [x] Install PostgreSQL client (psql or pgAdmin)
- [x] Verify Python 3.x is installed
- [x] Ensure access to Mobilize CRM codebase

## Environment Setup Checklist

- [x] Install required Python packages:
  - [x] `pip install psycopg2-binary`

## Supabase Configuration Checklist

- [x] Login to Supabase dashboard
- [x] Navigate to Project Settings > Database
- [x] Record connection information:
  - [x] Host: `fwnitauuyzxnsvgsbrzr.supabase.co` (Note: Don't include `db.` prefix)
  - [x] Port: `5432`
  - [x] Database: `postgres`
  - [x] User: `postgres`
  - [x] Password: (from Supabase settings)

## Production Environment Setup Checklist

- [x] Create production environment file:
  - [x] `cp .env.development .env.production`
- [x] Update database connection strings in `.env.production`:
  - [x] Set `DATABASE_URL` to Supabase connection string
  - [x] Set `DB_CONNECTION_STRING` to Supabase connection string
  - [x] Generate secure `SECRET_KEY` for Flask
- [x] Confirm all other environment variables are properly set

## Database Schema Migration Checklist

- [x] Set up production environment variables:
  - [x] `export FLASK_APP=app.py`
  - [x] `export FLASK_ENV=production`
  - [x] `export DATABASE_URL=postgresql://postgres:[PASSWORD]@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres`
- [ ] Apply database migrations:
  - [ ] Modify migration script to handle NOT NULL constraints if needed
  - [ ] `flask db upgrade` (Note: Encountered NOT NULL constraint issues)
- [ ] Verify schema was created successfully

## Data Migration Checklist

- [ ] Create `migrate_data.py` script using the template provided
- [ ] **IMPORTANT**: Add data cleaning/validation to handle NULL values:
  ```python
  # Example modification to add to transfer_table function
  # When preparing data for PostgreSQL, set default values for NOT NULL columns
  for row in rows:
      row_data = []
      for i, col in enumerate(columns):
          value = row[i]
          # Handle NULL values for NOT NULL constraints
          if value is None:
              if col == 'date_created' or col == 'date_modified':
                  value = datetime.utcnow()  # Use current timestamp
              elif col.endswith('_enabled') or col.startswith('is_') or col in ['virtuous', 'has_conflict']:
                  value = False  # Default boolean
              elif col == 'type':
                  value = 'unknown'  # Default string
          
          # Handle SQLite boolean conversion
          if isinstance(value, int) and (col.endswith('_enabled') or col.startswith('is_') or col in ['virtuous', 'has_conflict']):
              row_data.append(bool(value))
          else:
              row_data.append(value)
  ```
- [ ] Verify table list in the script matches your database tables
- [ ] Run the migration script:
  - [ ] `python migrate_data.py`
- [ ] Monitor for errors during execution

## Verification Checklist

- [ ] Connect to Supabase PostgreSQL:
  - [ ] `psql "postgresql://postgres:[YOUR-PASSWORD]@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres"`
- [ ] Verify data was transferred correctly:
  - [ ] Check user count: `SELECT COUNT(*) FROM users;`
  - [ ] Check contacts count: `SELECT COUNT(*) FROM contacts;`
  - [ ] Check people count: `SELECT COUNT(*) FROM people;`
  - [ ] Verify other important tables
- [ ] Compare counts with SQLite database for consistency

## Final Configuration Checklist

- [ ] Update production `.env` file:
  - [ ] Confirm `DATABASE_URL` is correct
  - [ ] Confirm `DB_CONNECTION_STRING` is correct
  - [ ] Set `SKIP_DB_INIT=True`
- [ ] Prepare for deployment:
  - [ ] Set up secrets in GCP Secret Manager
  - [ ] Configure deployment to use Supabase PostgreSQL

## Troubleshooting Preparation

- [ ] Document commands for handling foreign key constraints:
  - [ ] `SET session_replication_role = 'replica';` (disable)
  - [ ] `SET session_replication_role = 'origin';` (enable)
- [ ] Prepare for data type conversion issues:
  - [ ] Review date/time fields for PostgreSQL compatibility
  - [ ] Check boolean fields (0/1 in SQLite vs. true/false in PostgreSQL)
  - [ ] Review TEXT fields that might have VARCHAR limits in PostgreSQL

## Post-Migration Checklist

- [ ] Run comprehensive application tests:
  - [ ] Test all core features
  - [ ] Verify all data relationships are preserved
  - [ ] Check query performance
- [ ] Set up automated backups for Supabase database
- [ ] Configure optimal PostgreSQL settings:
  - [ ] Adjust connection pooling in Supabase > Database > Configuration

## Final Deployment Checklist

- [ ] Follow deployment instructions in `docs/deployment-guide.md`
- [ ] Verify application works with PostgreSQL in production
- [ ] Monitor application logs for database-related errors 