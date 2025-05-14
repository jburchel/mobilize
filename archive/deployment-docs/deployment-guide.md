# Mobilize CRM Deployment Guide

This document provides instructions for deploying the Mobilize CRM application to a production environment.

## Prerequisites

- Google Cloud Platform (GCP) account
- Supabase PostgreSQL database
- Domain name (optional, but recommended for production)
- Git repository for the application

## Deployment Steps

### 1. Prepare the Database

Before deployment, ensure your PostgreSQL database is set up and migrated:

1. Follow the instructions in `docs/sqlite_to_postgres_migration.md` to set up your Supabase PostgreSQL database
2. Verify that the database schema and data have been properly migrated

### 2. Set Up Google Cloud Platform

#### Create a GCP Project

1. Sign in to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note the Project ID for later use

#### Enable Required APIs

Enable the following APIs:
- Cloud Run API
- Secret Manager API
- Cloud SQL Admin API
- Cloud Build API

```bash
# Enable required APIs
gcloud services enable run.googleapis.com secretmanager.googleapis.com sqladmin.googleapis.com cloudbuild.googleapis.com
```

### 3. Create Environment Variables in Secret Manager

Store your environment variables in GCP Secret Manager:

```bash
# Create secrets for each environment variable
gcloud secrets create mobilize-db-url --data-file=- <<< "postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-ID].supabase.co:5432/postgres"
gcloud secrets create mobilize-flask-secret --data-file=- <<< "your-secure-flask-secret-key"
gcloud secrets create mobilize-google-client-id --data-file=- <<< "your-google-client-id"
gcloud secrets create mobilize-google-client-secret --data-file=- <<< "your-google-client-secret"
# Add other required secrets...
```

### 4. Prepare Application for Deployment

1. Create an `.env.production` file with your production settings
2. Create a `Dockerfile` in the root of your project:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# The database URL will be injected from Secret Manager

# Expose port for Cloud Run
EXPOSE 8080

# Run gunicorn
CMD exec gunicorn --bind :8080 --workers 1 --threads 8 --timeout 0 app:app
```

3. Update `requirements.txt` to include deployment dependencies:

```
# Add these to your existing requirements.txt
gunicorn==20.1.0
psycopg2-binary==2.9.6
google-cloud-secret-manager==2.16.1
```

4. Create a `cloudbuild.yaml` file in the root of your project:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/mobilize-crm:$COMMIT_SHA', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/mobilize-crm:$COMMIT_SHA']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'mobilize-crm'
      - '--image'
      - 'gcr.io/$PROJECT_ID/mobilize-crm:$COMMIT_SHA'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--set-secrets'
      - 'DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest,GOOGLE_CLIENT_ID=mobilize-google-client-id:latest,GOOGLE_CLIENT_SECRET=mobilize-google-client-secret:latest'

images:
  - 'gcr.io/$PROJECT_ID/mobilize-crm:$COMMIT_SHA'
```

### 5. Modify `app.py` to use Secret Manager in Production

Add code to dynamically fetch secrets from Secret Manager in production:

```python
import os
from flask import Flask

app = Flask(__name__)

# Load configuration based on environment
if os.environ.get('FLASK_ENV') == 'production':
    # In production, load secrets from Secret Manager
    from google.cloud import secretmanager
    
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    client = secretmanager.SecretManagerServiceClient()
    
    def access_secret(secret_id):
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    
    # Load secrets
    app.config['SECRET_KEY'] = access_secret('mobilize-flask-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = access_secret('mobilize-db-url')
    app.config['GOOGLE_CLIENT_ID'] = access_secret('mobilize-google-client-id')
    app.config['GOOGLE_CLIENT_SECRET'] = access_secret('mobilize-google-client-secret')
else:
    # In development, load from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# Rest of your app initialization...
```

### 6. Deploy to Cloud Run

Deploy using one of these methods:

#### Option 1: Manual Deployment

```bash
# Build the Docker image
docker build -t gcr.io/[YOUR-PROJECT-ID]/mobilize-crm:latest .

# Push to Google Container Registry
docker push gcr.io/[YOUR-PROJECT-ID]/mobilize-crm:latest

# Deploy to Cloud Run
gcloud run deploy mobilize-crm \
  --image gcr.io/[YOUR-PROJECT-ID]/mobilize-crm:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest,GOOGLE_CLIENT_ID=mobilize-google-client-id:latest,GOOGLE_CLIENT_SECRET=mobilize-google-client-secret:latest
```

#### Option 2: Continuous Deployment

1. Connect your Git repository to Cloud Build:
   - Go to Cloud Build > Triggers
   - Click "Create Trigger"
   - Connect to your Git repository
   - Configure the trigger to use the `cloudbuild.yaml` file
   - Set the trigger to run on commits to your main/master branch

2. Push to your repository to trigger a deployment:
   ```bash
   git add .
   git commit -m "Ready for production deployment"
   git push origin main
   ```

### 7. Set Up Custom Domain (Optional)

1. Go to Cloud Run > Select your service
2. Click "Domain Mappings" > "Add Mapping"
3. Follow the instructions to verify domain ownership and set up DNS records

### 8. Configure SSL (Automatic with Cloud Run)

Cloud Run automatically provisions SSL certificates for custom domains.

### 9. Set Up Monitoring and Logging

1. In the GCP Console, go to Monitoring > Dashboards
2. Create a custom dashboard for your Cloud Run service
3. Set up alerting for CPU usage, memory, and error rates

### 10. Post-Deployment Verification

1. Visit your deployed application URL
2. Verify that all features work as expected
3. Check that database connections are working properly
4. Test user authentication flows

## Troubleshooting

### Application Crashes

If the application crashes after deployment:

1. Check Cloud Run logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm"
   ```

2. Verify environment variables are set correctly:
   ```bash
   gcloud run services describe mobilize-crm
   ```

### Database Connection Issues

If the application can't connect to the database:

1. Check that the correct DATABASE_URL is set in Secret Manager
2. Verify that Supabase PostgreSQL is allowing connections from Cloud Run's IP range
3. Test the connection using a script deployed to Cloud Run

### Performance Tuning

For better performance:

1. Adjust Cloud Run settings:
   ```bash
   gcloud run services update mobilize-crm --memory 1Gi --cpu 1
   ```

2. Configure PostgreSQL connection pooling in Supabase

## Maintenance

### Regular Database Backups

Set up scheduled backups for your Supabase database:

1. Go to Supabase > Database > Backups
2. Configure daily backups

### Updating the Application

To update your deployed application:

1. Make changes to your code
2. Build and deploy a new version following the steps above
3. Monitor the deployment to ensure it works as expected 