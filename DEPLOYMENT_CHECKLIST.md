# SQLite to PostgreSQL Migration & Cloud Deployment Checklist
**Completed: April 21, 2025**

## Pre-Deployment Tasks

- [x] **Google Cloud Platform (GCP) Project Setup**
  - [x] Create/select a GCP project
  - [x] Enable required APIs: Cloud Run, Secret Manager, Cloud SQL Admin, Cloud Build

- [x] **Environment Setup**
  - [x] Update `.env.production` file with PostgreSQL connection string
  - [x] Install required packages: `psycopg2-binary`, `python-dotenv`
  - [x] Verify Python version compatibility (3.8+)

- [x] **Secret Manager Setup**
  - [x] Store database and app secrets in GCP Secret Manager using `gcloud secrets create ...`
  - [x] Grant service account access to secrets

- [x] **Migration Files Analysis**
  - [x] Run `python3 pg_migration_sql_commands.py` to analyze the latest migration
  - [x] Review SQL commands for PostgreSQL compatibility
  - [x] Check for any SQLite-specific functions or syntax
  - [x] Verify all migration files for potential issues (implicit column combinations, etc.)

- [x] **Database Backup**
  - [x] Create backup of SQLite database
  - [x] Document current database schema (tables, columns, constraints)
  - [x] Export critical data to CSV for verification later (Not needed for production as we're using dummy data)

## Deployment Tasks

- [x] **PostgreSQL Setup**
  - [x] Verify PostgreSQL connection string works
  - [x] Ensure database user has appropriate permissions
  - [x] Configure PostgreSQL for the application needs (connection pool size, etc.)

- [x] **Schema Migration**
  - [x] Initialize the migration environment: `flask db init` with PostgreSQL connection
  - [x] Generate a migration script for the current state: `flask db migrate`
  - [x] Review the generated migration for accuracy
  - [x] Apply migration to PostgreSQL: `flask db upgrade`

- [x] **Data Migration**
  - [x] Transfer data from SQLite to PostgreSQL
  - [x] Verify data integrity after migration
  - [x] Check relationships and constraints are maintained
  - [x] Verify primary keys and sequences are correctly set

- [x] **Application Configuration**
  - [x] Update application configuration to use PostgreSQL
  - [x] Set appropriate connection pool settings
  - [x] Configure environment variables for production

- [x] **Docker & Build Setup**
  - [x] Create/update `Dockerfile` for production
  - [x] Update `requirements.txt` with deployment dependencies
  - [x] Create/update `cloudbuild.yaml` for CI/CD

- [x] **Modify app.py for Production Secrets**
  - [x] Add code to load secrets from Secret Manager in production

- [x] **Testing**
  - [x] Test application functionality with PostgreSQL
  - [x] Verify CRUD operations work correctly
  - [x] Test performance with expected load
  - [x] Check for any degradation in query performance

## Deployment & Post-Deployment Tasks

- [x] **Application Deployment**
  - [x] Deploy updated application using Cloud Build or manual Docker/GCP commands
  - [x] Verify service account permissions
  - [x] Check application starts correctly
  - [x] Monitor for any startup errors

- [x] **Monitoring & Logging**
  - [x] Set up database monitoring
  - [x] Configure alerts for database issues
  - [x] Monitor application logs for database-related errors
  - [x] Use GCP logging commands to troubleshoot deployment issues

- [x] **Rollback Plan**
  - [x] Document rollback procedure
  - [x] Keep SQLite database available as fallback
  - [x] Have configuration ready to switch back if needed

- [x] **Validation**
  - [x] Verify all application features work with PostgreSQL
  - [x] Check data consistency
  - [x] Run automated tests against PostgreSQL database
  - [x] Verify all background jobs run correctly

## Cloud Run Specific Tasks

- [x] **Service Configuration**
  - [x] Update Cloud Run service configuration if needed
  - [x] Set appropriate memory and CPU allocation
  - [x] Configure scaling parameters
  - [x] Set port to 8080 for Cloud Run compatibility

- [x] **Secret Management**
  - [x] Store database credentials in Secret Manager
  - [x] Grant service account access to secrets
  - [x] Configure the application to use secrets

- [x] **Networking**
  - [x] Configure VPC connector if needed for private networking
  - [x] Set up Serverless VPC Access if required
  - [x] Configure Cloud SQL proxy if using Cloud SQL

- [x] **Custom Domain & SSL (Optional)**
  - [x] Set up custom domain mapping in Cloud Run
  - [x] Verify automatic SSL provisioning

## Final Verification

- [x] **End-to-End Testing**
  - [x] Perform end-to-end testing of critical workflows
  - [x] Verify user authentication flows
  - [x] Test data synchronization features
  - [x] Check reporting and analytics features

- [x] **Performance Analysis**
  - [x] Compare performance metrics with SQLite
  - [x] Optimize slow queries if needed
  - [x] Analyze database connection patterns

- [x] **Documentation Update**
  - [x] Update project documentation with PostgreSQL and deployment details
  - [x] Document any configuration changes
  - [x] Update maintenance procedures for PostgreSQL and Cloud Run

- [x] **Troubleshooting**
  - [x] Reference GCP logs and deployment guide for troubleshooting tips 