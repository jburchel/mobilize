# Mobilize CRM Deployment Guide

This guide provides instructions for deploying the Mobilize CRM application to Google Cloud Run. The deployment process has been simplified to ensure consistency between local development and production environments.

## Prerequisites

- Google Cloud SDK installed and configured
- Docker installed locally (for testing)
- Access to the Google Cloud project `mobilize-crm`
- Proper permissions to deploy to Cloud Run and access Secret Manager

## Deployment Files

The deployment configuration is contained in the following files:

- `deploy/Dockerfile` - Container configuration
- `deploy/cloudbuild.yaml` - Cloud Build configuration
- `deploy/scripts/deploy.sh` - Deployment script
- `deploy/scripts/check_logs.sh` - Log checking utility

## Deployment Options

### Option 1: Automated Deployment via Cloud Build

This is the recommended approach for production deployments.

1. Push your changes to the main branch of your repository
2. Cloud Build will automatically trigger a build and deployment
3. Monitor the build progress in the Google Cloud Console

### Option 2: Manual Deployment using gcloud

For testing or when you need more control over the deployment process:

1. Make the deployment scripts executable:
   ```bash
   chmod +x deploy/scripts/deploy.sh deploy/scripts/check_logs.sh
   ```

2. Run the deployment script with the desired options:
   ```bash
   # Standard deployment (immediate traffic)
   ./deploy/scripts/deploy.sh
   
   # Safe deployment (no immediate traffic)
   ./deploy/scripts/deploy.sh --safe-deploy
   
   # Update only environment variables
   ./deploy/scripts/deploy.sh --env-only
   
   # Update only secrets
   ./deploy/scripts/deploy.sh --secrets-only
   ```

## Checking Logs

Use the log checking script to view logs from your Cloud Run service:

```bash
# View INFO level logs from the last hour
./deploy/scripts/check_logs.sh

# View ERROR level logs from the last day
./deploy/scripts/check_logs.sh --severity ERROR --freshness 1d

# View the last 50 log entries
./deploy/scripts/check_logs.sh --limit 50
```

## Troubleshooting Production Issues

If your application is working locally but not in production, follow these steps:

1. Check for errors in the logs:
   ```bash
   ./deploy/scripts/check_logs.sh --severity ERROR
   ```

2. Compare environment variables between local and production:
   - Local: Check your `.env` or `.flaskenv` file
   - Production: View in the Cloud Run console or use `gcloud run services describe mobilize-crm`

3. Verify secrets are properly set in Secret Manager and accessible to your service account

4. Test with a safe deployment to isolate issues:
   ```bash
   ./deploy/scripts/deploy.sh --safe-deploy
   ```

5. Check for differences in dependencies:
   - Ensure your `requirements.txt` file is up to date
   - Verify the Python version matches between environments

## Common Issues and Solutions

### Database Connection Issues

- Verify the `DATABASE_URL` secret is correctly set in Secret Manager
- Ensure your Cloud Run service account has access to the database
- Check for network connectivity issues (e.g., firewall rules)

### Authentication Problems

- Verify the `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` secrets are correctly set
- Check that the redirect URIs are properly configured in the Google Cloud Console
- Ensure Firebase configuration is correct if using Firebase Authentication

### Performance Issues

- Consider adjusting the Cloud Run configuration (CPU, memory, concurrency)
- Check for slow database queries or external API calls
- Enable caching where appropriate

## Monitoring and Maintenance

- Set up Cloud Monitoring alerts for errors and performance issues
- Regularly check logs for warnings and errors
- Keep dependencies updated
- Consider implementing a CI/CD pipeline for automated testing and deployment

## Local vs. Production Differences

Key differences between local development and production:

1. **Environment**: Production uses `FLASK_ENV=production` which disables debug mode
2. **Database**: Production connects to a Cloud SQL instance instead of a local database
3. **Logging**: Production logs are sent to Cloud Logging
4. **Serving**: Production uses Gunicorn with multiple workers instead of Flask's development server
5. **HTTPS**: Production enforces HTTPS via `PREFERRED_URL_SCHEME=https`

## Rollback Procedure

If a deployment causes issues, you can quickly roll back to a previous version:

```bash
# List available revisions
gcloud run revisions list --service=mobilize-crm --region=us-central1

# Roll back to a specific revision
gcloud run services update-traffic mobilize-crm --region=us-central1 --to-revisions=REVISION_NAME=100
```

Replace `REVISION_NAME` with the name of the revision you want to roll back to.
