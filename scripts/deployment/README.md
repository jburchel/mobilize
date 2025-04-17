# Mobilize CRM Deployment

This directory contains scripts and configurations for deploying the Mobilize CRM application to Google Cloud Run.

## Available Scripts

- `entrypoint.sh`: Docker container entrypoint script that handles database migrations and starts the application
- `cloudbuild.yaml`: Google Cloud Build configuration for CI/CD pipeline
- `ci-cd.yml`: GitHub Actions workflow for testing and deployment

## Deployment Process

To deploy the application, follow these steps:

1. Set up the required Google Cloud resources as detailed in the `/docs/deployment-guide.md` file
2. Create a production `.env` file based on the `.env.production.template`
3. Store sensitive environment variables in Google Cloud Secret Manager
4. Set up the CI/CD pipeline to deploy automatically from the main branch

### Manual Deployment

If you need to deploy manually:

1. Build the Docker container:
   ```bash
   docker build -t gcr.io/YOUR_PROJECT_ID/mobilize-app:latest .
   ```

2. Push the container image:
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/mobilize-app:latest
   ```

3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy mobilize-app \
     --image gcr.io/YOUR_PROJECT_ID/mobilize-app:latest \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --memory 1Gi \
     --cpu 1 \
     --min-instances 1 \
     --max-instances 10 \
     --set-env-vars FLASK_ENV=production \
     --set-cloudsql-instances YOUR_PROJECT_ID:us-central1:mobilize-db \
     --set-secrets=/app/.env=mobilize-app-env:latest
   ```

### Database Migrations

Database migrations are automatically applied on container startup. If you need to run migrations manually:

```bash
gcloud run jobs create mobilize-db-migrate \
  --image gcr.io/YOUR_PROJECT_ID/mobilize-app:latest \
  --region us-central1 \
  --set-cloudsql-instances YOUR_PROJECT_ID:us-central1:mobilize-db \
  --set-secrets=/app/.env=mobilize-app-env:latest \
  --command "flask" \
  --args "db,upgrade"
```

### Rollback Procedure

To rollback to a previous version of the application:

1. Identify the image tag of the working version
2. Redeploy Cloud Run service with that image:
   ```bash
   gcloud run deploy mobilize-app \
     --image gcr.io/YOUR_PROJECT_ID/mobilize-app:WORKING_TAG \
     --region us-central1
   ```

## For More Information

See the following documentation for more details:

- `/docs/deployment-guide.md`: Comprehensive deployment guide
- `/docs/api-documentation.md`: API reference documentation
- `/docs/user-manual.md`: User manual for the application

## Monitoring and Troubleshooting

For monitoring and troubleshooting in production:

1. View application logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-app" --limit=10
   ```

2. Check for error rates in Google Cloud Monitoring
3. Verify database connectivity using Cloud SQL Admin
4. Check deployment history in Cloud Run console 