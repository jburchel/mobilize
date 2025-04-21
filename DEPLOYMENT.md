# Mobilize CRM Deployment Guide
## SQLite to PostgreSQL Migration

This document outlines the steps required to deploy the Mobilize CRM application and migrate data from SQLite to PostgreSQL.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database (Supabase or other provider)
- Access to both development (SQLite) and production environments
- Required Python packages: `psycopg2-binary`, `python-dotenv`, `flask-migrate`

## Migration Options

There are two migration options depending on your specific situation:

1. **SQLite to PostgreSQL Migration**: Use this if you are migrating from a local SQLite database to Supabase PostgreSQL
2. **Render to Supabase Migration**: Use this if you are migrating from an existing Render PostgreSQL database to Supabase PostgreSQL

Choose the appropriate migration path based on your current database setup.

## Option 1: SQLite to PostgreSQL Migration

### Step 1: Environment Setup

1. Create a `.env.production` file with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@host:port/database
   FLASK_ENV=production
   SECRET_KEY=your_secret_key
   ```

2. Install required dependencies:
   ```bash
   pip install psycopg2-binary python-dotenv
   ```

### Step 2: Generate PostgreSQL Migration

1. Create a PostgreSQL-compatible migration file:
   ```bash
   # If using alembic directly
   FLASK_APP=app.py flask db migrate -m "production_ready_schema"
   
   # Or run the pg_migration_test.py script to preview SQL
   python pg_migration_test.py
   ```

2. Verify the generated migration file in the `migrations/versions/` directory.

### Step 3: Database Migration

1. Run the data migration script to transfer data from SQLite to PostgreSQL:
   ```bash
   python migrate_data.py
   ```

2. The script performs the following operations:
   - Connects to both SQLite and PostgreSQL databases
   - Transfers table data in the correct order (respecting foreign key constraints)
   - Handles data type conversions and NULL values
   - Resets sequence values for auto-incrementing columns
   - Reports on the migration progress

### Step 4: Data Validation

1. Run the post-migration validation script:
   ```bash
   python post_migration_checks.py
   ```

2. The validation script checks for:
   - Table row counts
   - Foreign key violations
   - NULL values in critical columns
   - Data integrity issues (duplicate emails, orphaned records, etc.)

3. If issues are found, review the generated `data_fixes.sql` file and apply fixes as needed:
   ```bash
   psql -h hostname -U username -d database -f data_fixes.sql
   ```

## Option 2: Render to Supabase PostgreSQL Migration

This option is for users who already have data in a Render PostgreSQL database and need to migrate to Supabase PostgreSQL.

### Step 1: Setup Migration Environment

1. Run the setup script to configure the migration environment:
   ```bash
   python setup_render_migration.py
   ```

2. The script will:
   - Prompt for your Render PostgreSQL connection string
   - Create or update `.env.production` with both database URLs
   - Generate a migration mappings template file
   - Check for required dependencies

### Step 2: Compare Database Schemas

1. Run the schema comparison tool to identify differences between databases:
   ```bash
   python schema_comparison.py
   ```

2. Review the generated `schema_diff_report.txt` file to understand:
   - Tables present in one database but not the other
   - Column differences between databases
   - Primary key and foreign key differences
   - Suggested column mappings for tables with schema differences

3. Update the `migration_mappings.py` file with any necessary mappings based on the schema comparison results.

### Step 3: Run Migration

1. Perform a dry run first to preview the migration without making changes:
   ```bash
   python migrate_render_to_supabase.py --dry-run
   ```

2. Review the output to ensure the migration plan looks correct.

3. Run the actual migration:
   ```bash
   python migrate_render_to_supabase.py
   ```

4. The script will:
   - Connect to both Render and Supabase databases
   - Migrate data table by table in the correct order
   - Apply any column mappings or transformations specified in `migration_mappings.py`
   - Reset sequence values for identity columns
   - Generate a detailed migration report

### Step 4: Data Validation

1. Run the post-migration validation script:
   ```bash
   python post_migration_checks.py
   ```

2. The validation script checks for:
   - Table row counts
   - Foreign key violations
   - NULL values in critical columns
   - Data integrity issues (duplicate emails, orphaned records, etc.)

3. If issues are found, review the generated `data_fixes.sql` file and apply fixes as needed:
   ```bash
   psql -h hostname -U username -d database -f data_fixes.sql
   ```

## Migration Success Summary

The migration from Render SQLite to Supabase PostgreSQL has been completed successfully. The following data has been migrated:

| Table | Records | Notes |
|-------|---------|-------|
| Contacts | 270 | 13 new records added during migration |
| Tasks | 23 | 15 new records added during migration |
| Communications | 7,951 | All existing in Supabase |
| Churches | 97 | No new records due to schema constraints |
| People | 160 | No new records due to schema constraints |

The application is now ready to be configured to use the Supabase PostgreSQL database as its primary data store. Update your database connection strings in your application configuration to point to the Supabase database URL:

```
postgresql://postgres.fwnitauuyzxnsvgsbrzr:RV4QOygx0LpqOjzx@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

This connection string uses the Supavisor pooler which provides better compatibility with IPv4 networks and handles connection pooling efficiently.

## Application Configuration

1. Update your application configuration to use PostgreSQL:
   ```python
   # config.py or similar
   SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
   ```

2. Update any database-specific code to be compatible with PostgreSQL syntax.

## Application Deployment

1. Set up your production environment (e.g., AWS, Heroku, DigitalOcean).

2. Deploy your application code to the production server.

3. Configure your web server (e.g., Gunicorn, uWSGI) and reverse proxy (e.g., Nginx).

4. Set up SSL certificates for secure connections.

## Post-Deployment Tasks

1. Create a production admin user if needed:
   ```bash
   flask create-admin --email admin@example.com --password secure_password
   ```

2. Configure backup schedules for your PostgreSQL database.

3. Set up monitoring for your application and database.

## Troubleshooting

### Common Migration Issues

1. **Data Type Incompatibilities**: 
   - SQLite is loosely typed while PostgreSQL is strongly typed
   - Check for type conversion issues in the migration logs
   - Use explicit type casts in problematic SQL statements

2. **Foreign Key Constraints**:
   - PostgreSQL enforces foreign key constraints more strictly
   - Check for constraint violations in the validation report
   - Fix orphaned records before using the application

3. **Case Sensitivity**:
   - PostgreSQL is case-sensitive for table and column names
   - Ensure consistent case usage in your application code

4. **Sequence Issues**:
   - After migration, PostgreSQL sequences might not be synced
   - Use the `reset_sequences` function in the migration script

5. **Schema Differences in Render to Supabase Migration**:
   - Different column names or types between databases
   - Missing or additional columns
   - Different constraint definitions
   - Use the `migration_mappings.py` file to handle these differences

### Rollback Plan

In case of failed migration:

1. Keep your original database (SQLite or Render PostgreSQL) as a backup
2. Document all changes made during the migration
3. Have a script ready to restore from your latest backup

## Maintenance Tasks

1. Regular database maintenance:
   ```bash
   # Analyze database statistics
   ANALYZE;
   
   # Vacuum to reclaim space and optimize
   VACUUM FULL;
   ```

2. Schedule regular backups:
   ```bash
   # Example using pg_dump
   pg_dump -h hostname -U username -d database > backup_$(date +%Y%m%d).sql
   ```

3. Monitor database performance and growth over time.

## Additional Resources

- [Supabase PostgreSQL Documentation](https://supabase.com/docs/guides/database)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Cloud Deployment Notes

When deploying to Google Cloud Run using Cloud Build, ensure that the Cloud Build service account has the appropriate IAM permissions. Here are the complete steps needed:

1. First, identify your Cloud Build service account (typically PROJECT_NUMBER@cloudbuild.gserviceaccount.com) and Compute service account (typically PROJECT_NUMBER-compute@developer.gserviceaccount.com):
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID --format=json | grep serviceAccount
   ```

2. Grant the Cloud Build service account the `iam.serviceAccountUser` role for the Compute service account:
   ```bash
   gcloud iam service-accounts add-iam-policy-binding PROJECT_NUMBER-compute@developer.gserviceaccount.com --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com --role=roles/iam.serviceAccountUser
   ```

3. Grant the Cloud Build service account the `iam.serviceAccountUser` role at the project level:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com --role=roles/iam.serviceAccountUser
   ```

4. Grant the Cloud Build service account the `run.admin` role:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com --role=roles/run.admin
   ```

5. Grant the Cloud Build service account the `run.serviceAgent` role:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com --role=roles/run.serviceAgent
   ```

All these permissions are required for Cloud Build to successfully deploy to Cloud Run.

### Cloud Build Trigger Configuration

When creating a Cloud Build trigger, use the same service account that will be used for the Cloud Run deployment. This ensures consistent permissions between the build and deployment:

1. In the Cloud Build trigger configuration, select the custom service account option.
2. Choose the same service account specified in the `--service-account` parameter in the `cloudbuild.yaml` file.
3. Ensure this service account has all the necessary permissions:
   - `roles/cloudbuild.builds.builder`
   - `roles/iam.serviceAccountUser`
   - `roles/run.admin`
   - `roles/run.serviceAgent`
   - `roles/storage.admin`
   - `roles/artifactregistry.writer`

### Database Connection Issues

#### Supabase Connection Strings

Supabase provides multiple connection formats:

1. **Direct Connection** (default): 
   ```
   postgresql://postgres:[PASSWORD]@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres
   ```

2. **Without `db.` prefix** (if DNS resolution fails):
   ```
   postgresql://postgres:[PASSWORD]@fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres
   ```

3. **With SSL required**:
   ```
   postgresql://postgres:[PASSWORD]@db.fwnitauuyzxnsvgsbrzr.supabase.co:5432/postgres?sslmode=require
   ```

4. **Supavisor Connection Pooler** (recommended for most use cases):
   ```
   postgresql://postgres.fwnitauuyzxnsvgsbrzr:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```

After extensive testing, we determined that the **Supavisor Connection Pooler** (option 4) provides the most reliable connection, especially when dealing with IPv4/IPv6 compatibility issues.

If you're experiencing connection issues:
- Use the Supavisor Connection Pooler (option 4) as your primary connection method
- Check if your IP is allowed in Supabase's database settings
- Verify that port 5432 is not blocked by your firewall
- Consider using the Supabase JS client instead of direct PostgreSQL connections 