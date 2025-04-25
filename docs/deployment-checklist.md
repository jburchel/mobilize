# Mobilize CRM Deployment Checklist

## 1. Database Preparation

- [x] Set up Supabase PostgreSQL database
  - [x] Obtain Supabase connection details (host, port, database name, username, password)
  - [x] Test connection to Supabase database
- [x] Complete SQLite to PostgreSQL migration
  - [x] Follow instructions in `docs/sqlite_to_postgres_migration.md`
  - [x] Use `pg_migration_test_final.py` script to preview SQL migration commands
  - [x] Verify database schema was properly created
  - [x] Confirm all data was migrated successfully
  - [x] Run validation queries to check data integrity

## 2. Google Cloud Platform Setup

- [x] Create or select GCP Project
  - [x] Record Project ID: mobilize-crm
- [x] Enable required APIs
  - [x] Cloud Run API
  - [x] Secret Manager API
  - [x] Cloud SQL Admin API
  - [x] Cloud Build API
  - [x] Run command: `gcloud services enable run.googleapis.com secretmanager.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com`
- [x] Confirm billing is enabled for the project

## 3. Environment Variables and Secrets

- [x] Create production environment variables file
  - [x] Copy `.env.development` to `.env.production`
  - [x] Update database connection string for Supabase
  - [x] Generate secure Flask SECRET_KEY
  - [x] Update all other environment variables for production
- [x] Store secrets in GCP Secret Manager
  - [x] Database URL: `gcloud secrets create mobilize-db-url --data-file=- <<< "postgresql://postgres:[PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres"`
  - [x] Flask secret key: `gcloud secrets create mobilize-flask-secret --data-file=- <<< "[SECURE-RANDOM-KEY]"`
  - [x] Google client ID: `gcloud secrets create mobilize-google-client-id --data-file=- <<< "[YOUR-GOOGLE-CLIENT-ID]"`
  - [x] Google client secret: `gcloud secrets create mobilize-google-client-secret --data-file=- <<< "[YOUR-GOOGLE-CLIENT-SECRET]"`
  - [x] Add any other required secrets

## 4. Application Preparation

- [x] Update requirements.txt with deployment dependencies
  - [x] Add `gunicorn==20.1.0` (already in requirements.txt)
  - [x] Add `psycopg2-binary==2.9.6` (using psycopg instead)
  - [x] Add `google-cloud-secret-manager==2.16.1` (added in Dockerfile)
- [x] Create Dockerfile in project root
  - [x] Base image: Python 3.10-slim
  - [x] Set up working directory and copy files
  - [x] Install dependencies
  - [x] Configure environment variables
  - [x] Expose port 8080
  - [x] Set up gunicorn command
- [x] Create cloudbuild.yaml for CI/CD
  - [x] Configure build steps
  - [x] Set up image pushing
  - [x] Configure Cloud Run deployment
  - [x] Set up secret injection
- [x] Modify app.py to use Secret Manager in production
  - [x] Add code to detect production environment
  - [x] Implement secret fetching from Secret Manager
  - [x] Ensure fallback to .env for development

## 5. Deployment Process

- [x] Choose deployment method:
  - [ ] Option 1: Manual Deployment
  - [x] Option 2: Continuous Deployment
  - [x] Connect Git repository to Cloud Build
  - [x] Create build trigger for main/master branch
  - [x] Verify cloudbuild.yaml is properly configured
  - [x] Push code to repository to trigger deployment

**Note:** Continuous Deployment has been successfully set up! The GitHub repository (jburchel/mobilize) is connected to Cloud Build with a trigger named "Mobilize-Trigger" that will deploy on pushes to the main branch. The deployment process has been triggered and is currently running. You can monitor the progress in the Google Cloud Console under Cloud Build > History.

**Troubleshooting Steps Taken:**
1. Added permission roles to service account:
   - roles/logging.logWriter - For logging build output
   - roles/storage.admin - For accessing storage buckets
   - roles/containerregistry.ServiceAgent - For using Container Registry
   - roles/artifactregistry.writer - For pushing to Artifact Registry
   - roles/run.admin - For deploying to Cloud Run

2. Created Artifact Registry repository:
   - Command: `gcloud artifacts repositories create mobilize-crm --repository-format=docker --location=us-central1`

3. Updated cloudbuild.yaml to use Artifact Registry instead of Container Registry:
   - Changed image paths from `gcr.io/$PROJECT_ID/...` to `us-central1-docker.pkg.dev/$PROJECT_ID/mobilize-crm/...`

## 6. Domain Configuration (Optional)

- [ ] Set up custom domain in Cloud Run
  - [ ] Navigate to Domain Mappings in Cloud Run console
  - [ ] Add domain mapping
  - [ ] Verify domain ownership
  - [ ] Configure DNS records as instructed
- [ ] Verify SSL certificate is provisioned automatically

## 7. Monitoring and Logging Setup

- [ ] Set up monitoring dashboard in GCP Console
  - [ ] Add CPU usage metrics
  - [ ] Add memory usage metrics
  - [ ] Add request count metrics
  - [ ] Add error rate metrics
- [ ] Configure alerting policies
  - [ ] Set up alerts for high error rates
  - [ ] Configure alerts for resource usage thresholds
  - [ ] Set up email notifications for alerts
- [ ] Verify logging is properly configured
  - [ ] Check logs are being captured: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm"`

## 8. Post-Deployment Verification

- [ ] Access deployed application URL
  - [ ] Record the URL: ________________
- [ ] Verify all features work as expected
  - [ ] Test user authentication
  - [ ] Test contact management
  - [ ] Test task management
  - [ ] Test communication features
  - [ ] Test Google integration
  - [ ] Test pipeline management
  - [ ] Test reporting functions
- [ ] Verify database connections are working properly
- [ ] Check application logs for any errors

## 9. Backup and Recovery Planning

- [ ] Set up automated database backups in Supabase
- [ ] Document recovery procedures
- [ ] Test a restore from backup in a test environment

## 10. Documentation Updates

- [ ] Update README.md with production information
- [ ] Document deployment process
- [ ] Create runbook for common maintenance tasks
- [ ] Document troubleshooting procedures

## 11. Troubleshooting Guide

### Application Crashes
- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm"`
- Verify environment variables: `gcloud run services describe mobilize-crm`
- Check for Python exceptions in the logs

### Database Connection Issues
- Verify that the correct DATABASE_URL is set in Secret Manager
- Check that Supabase PostgreSQL is allowing connections from Cloud Run IP range
- Test connection using a script deployed to Cloud Run

### Authentication Problems
- Verify Google OAuth credentials are correct in Secret Manager
- Check that the redirect URIs include the production domain
- Verify that Firebase configuration is updated for production

## Notes and Completion
- Deployment date: ________________
- Deployed by: ________________
- Version/commit: ________________ 