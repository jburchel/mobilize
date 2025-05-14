# PostgreSQL Migration Deployment Plan

## Overview
This document outlines the steps to deploy the Mobilize CRM application with PostgreSQL to Google Cloud Run. This follows the SQLite to PostgreSQL migration preparations that have been completed.

## Pre-Deployment Summary
We have already:
- Created and configured a Supabase PostgreSQL database
- Updated application code to use PostgreSQL in production
- Migrated the database schema
- Created test scripts for validation
- Updated Docker and Cloud Build configuration files

## Deployment Steps

### 1. Set Up Cloud Build Trigger
1. Navigate to Cloud Build > Triggers in GCP Console
2. Create a new trigger for the repository
3. Configure it to use `cloudbuild.migrations.yaml` first, then `cloudbuild.yaml`
4. Set the branch to `main` or your production branch

### 2. Set Up GCP Secrets
1. Create or update the following secrets in Secret Manager:
   ```bash
   gcloud secrets create mobilize-db-url --data-file=/path/to/db-url.txt
   gcloud secrets create mobilize-flask-secret --data-file=/path/to/secret-key.txt
   gcloud secrets create firebase-credentials --data-file=/path/to/firebase-credentials.json
   ```

2. Grant access to the service account:
   ```bash
   gcloud secrets add-iam-policy-binding mobilize-db-url \
       --member=serviceAccount:mobilize-crm-service-account@mobilize-crm.iam.gserviceaccount.com \
       --role=roles/secretmanager.secretAccessor
   
   # Repeat for other secrets
   ```

### 3. Run Database Migrations
1. Trigger the migrations build:
   ```bash
   gcloud builds submit --config cloudbuild.migrations.yaml
   ```

2. Monitor the migration job:
   ```bash
   gcloud run jobs executions list --job migrate-db --region us-central1
   ```

3. Check migration logs for any errors

### 4. Deploy Application
1. Trigger the main application build:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

2. Monitor the build and deployment:
   ```bash
   gcloud builds list
   ```

### 5. Post-Deployment Testing
1. Verify the deployment in Cloud Run:
   ```bash
   gcloud run services describe mobilize-crm --region us-central1
   ```

2. Test the application by accessing:
   - Health check endpoint: `https://mobilize-crm.run.app/health`
   - API health check: `https://mobilize-crm.run.app/api/health-check`
   - Main application: `https://mobilize-crm.run.app/`

3. Run the CRUD and performance tests in the cloud environment:
   ```bash
   gcloud run jobs execute test-postgres-crud --region us-central1
   ```

### 6. Monitoring & Logging
1. Set up monitoring in Cloud Monitoring
2. Create alerts for:
   - Error rates above threshold
   - High database latency
   - Service outages

3. Review logs in Cloud Logging:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm" --limit 10
   ```

### 7. Rollback Plan
If issues are encountered:

1. Revert to SQLite:
   - Update `FLASK_ENV` to 'development' in Cloud Run service
   - Update `.env.production` file with SQLite connection

2. Roll back deployment:
   ```bash
   gcloud run services rollback mobilize-crm --region us-central1
   ```

## Validation Checklist
After deployment, verify:
- [ ] Application starts correctly
- [ ] Database connections are successful
- [ ] CRUD operations work properly
- [ ] Background jobs execute correctly
- [ ] Performance is acceptable
- [ ] Monitoring is in place

## Post-Deployment Documentation
Update project documentation with:
- PostgreSQL connection details
- Cloud Run deployment instructions
- Monitoring and alerting setup
- Backup and maintenance procedures

## Contact
For deployment issues, contact:
- Cloud Admin: [cloud-admin@example.com]
- Database Admin: [db-admin@example.com] 