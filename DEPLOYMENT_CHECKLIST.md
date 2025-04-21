# SQLite to PostgreSQL Migration Checklist

## Pre-Deployment Tasks

- [ ] **Environment Setup**
  - [ ] Update `.env.production` file with PostgreSQL connection string
  - [ ] Install required packages: `psycopg2-binary`, `python-dotenv`
  - [ ] Verify Python version compatibility (3.8+)

- [ ] **Migration Files Analysis**
  - [ ] Run `python3 pg_migration_sql_commands.py` to analyze the latest migration
  - [ ] Review SQL commands for PostgreSQL compatibility
  - [ ] Check for any SQLite-specific functions or syntax
  - [ ] Verify all migration files for potential issues (implicit column combinations, etc.)

- [ ] **Database Backup**
  - [ ] Create backup of SQLite database
  - [ ] Document current database schema (tables, columns, constraints)
  - [ ] Export critical data to CSV for verification later

## Deployment Tasks

- [ ] **PostgreSQL Setup**
  - [ ] Verify PostgreSQL connection string works
  - [ ] Ensure database user has appropriate permissions
  - [ ] Configure PostgreSQL for the application needs (connection pool size, etc.)

- [ ] **Schema Migration**
  - [ ] Initialize the migration environment: `flask db init` with PostgreSQL connection
  - [ ] Generate a migration script for the current state: `flask db migrate`
  - [ ] Review the generated migration for accuracy
  - [ ] Apply migration to PostgreSQL: `flask db upgrade`

- [ ] **Data Migration**
  - [ ] Transfer data from SQLite to PostgreSQL
  - [ ] Verify data integrity after migration
  - [ ] Check relationships and constraints are maintained
  - [ ] Verify primary keys and sequences are correctly set

- [ ] **Application Configuration**
  - [ ] Update application configuration to use PostgreSQL
  - [ ] Set appropriate connection pool settings
  - [ ] Configure environment variables for production

- [ ] **Testing**
  - [ ] Test application functionality with PostgreSQL
  - [ ] Verify CRUD operations work correctly
  - [ ] Test performance with expected load
  - [ ] Check for any degradation in query performance

## Post-Deployment Tasks

- [ ] **Application Deployment**
  - [ ] Deploy updated application using Cloud Build
  - [ ] Verify service account permissions
  - [ ] Check application starts correctly
  - [ ] Monitor for any startup errors

- [ ] **Monitoring**
  - [ ] Set up database monitoring
  - [ ] Configure alerts for database issues
  - [ ] Monitor application logs for database-related errors

- [ ] **Rollback Plan**
  - [ ] Document rollback procedure
  - [ ] Keep SQLite database available as fallback
  - [ ] Have configuration ready to switch back if needed

- [ ] **Validation**
  - [ ] Verify all application features work with PostgreSQL
  - [ ] Check data consistency
  - [ ] Run automated tests against PostgreSQL database
  - [ ] Verify all background jobs run correctly

## Cloud Run Specific Tasks

- [ ] **Service Configuration**
  - [ ] Update Cloud Run service configuration if needed
  - [ ] Set appropriate memory and CPU allocation
  - [ ] Configure scaling parameters
  - [ ] Set port to 8080 for Cloud Run compatibility

- [ ] **Secret Management**
  - [ ] Store database credentials in Secret Manager
  - [ ] Grant service account access to secrets
  - [ ] Configure the application to use secrets

- [ ] **Networking**
  - [ ] Configure VPC connector if needed for private networking
  - [ ] Set up Serverless VPC Access if required
  - [ ] Configure Cloud SQL proxy if using Cloud SQL

## Final Verification

- [ ] **End-to-End Testing**
  - [ ] Perform end-to-end testing of critical workflows
  - [ ] Verify user authentication flows
  - [ ] Test data synchronization features
  - [ ] Check reporting and analytics features

- [ ] **Performance Analysis**
  - [ ] Compare performance metrics with SQLite
  - [ ] Optimize slow queries if needed
  - [ ] Analyze database connection patterns

- [ ] **Documentation Update**
  - [ ] Update project documentation with PostgreSQL details
  - [ ] Document any configuration changes
  - [ ] Update maintenance procedures for PostgreSQL 