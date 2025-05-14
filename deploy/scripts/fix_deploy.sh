#!/bin/bash

set -e

# Mobilize CRM Fix Deployment Script
# This script handles the deployment process with special handling for existing environment variables

echo "===== Safe Deploying Mobilize CRM to Cloud Run ====="

# First, let's remove any conflicting environment variables
echo "Removing potentially conflicting environment variables..."
gcloud run services update mobilize-crm \
  --region us-central1 \
  --clear-env-vars

echo "Environment variables cleared. Proceeding with deployment..."

# Now deploy with our new configuration
echo "Performing safe deployment (no immediate traffic)..."
  
gcloud run deploy mobilize-crm \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --update-env-vars "FLASK_APP=app.py,FLASK_ENV=production,LOG_LEVEL=INFO,LOG_TO_STDOUT=True,PREFERRED_URL_SCHEME=https" \
  --update-secrets="DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest,FIREBASE_CREDENTIALS=firebase-credentials:latest,GOOGLE_CLIENT_ID=mobilize-google-client-id:latest,GOOGLE_CLIENT_SECRET=mobilize-google-client-secret:latest" \
  --cpu=1 \
  --memory=512Mi \
  --min-instances=1 \
  --max-instances=10 \
  --concurrency=80 \
  --timeout=300s \
  --no-traffic
  
echo "New revision deployed but not receiving traffic."
echo "Check the new revision for errors..."

# Wait a moment for the deployment to stabilize
sleep 10

# Check logs for errors
echo "Checking logs for errors in the new revision..."
ERROR_COUNT=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 5 --freshness=1m | grep -c "textPayload" || true)

if [ "$ERROR_COUNT" -gt 0 ]; then
  echo "WARNING: Found errors in the logs. Review before migrating traffic."
  gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 5 --freshness=1m
  
  read -p "Do you want to proceed with traffic migration? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment aborted. The new revision is deployed but not receiving traffic."
    exit 1
  fi
fi

# Migrate traffic to the new revision
echo "Migrating traffic to the new revision..."
gcloud run services update-traffic mobilize-crm \
  --region us-central1 \
  --to-latest
  
echo "Traffic successfully migrated to the new revision."

echo "Deployment complete!"

# Check for errors after deployment
echo "Checking for errors in logs..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 5 --freshness=1m
