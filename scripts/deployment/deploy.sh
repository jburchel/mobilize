#!/bin/bash

set -e

# Consolidated deployment script for Mobilize CRM
# This script handles all deployment tasks for the application

echo "===== Deploying Mobilize CRM to Cloud Run ====="

# Parse command line arguments
ENV_ONLY=false
SECRETS_ONLY=false
RESTART_ONLY=false
SAFE_DEPLOY=false  # New option for gradual traffic migration

while [[ $# -gt 0 ]]; do
  case $1 in
    --env-only)
      ENV_ONLY=true
      shift
      ;;
    --secrets-only)
      SECRETS_ONLY=true
      shift
      ;;
    --restart-only)
      RESTART_ONLY=true
      shift
      ;;
    --safe-deploy)
      SAFE_DEPLOY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--env-only] [--secrets-only] [--restart-only] [--safe-deploy]"
      exit 1
      ;;
  esac
done

# Environment variables to set
ENV_VARS="FLASK_APP=app,FLASK_ENV=production,PREFERRED_URL_SCHEME=https"

# Secrets to update
# Format: SECRET_ENV_VAR=SECRET_NAME:VERSION
# Using the actual secret names from the Google Cloud project
SECRETS="DB_CONNECTION_STRING=mobilize-db-connection-string:latest,GOOGLE_CLIENT_ID=mobilize-google-client-id:latest,GOOGLE_CLIENT_SECRET=mobilize-google-client-secret:latest,BASE_URL=BASE_URL:latest"

# Function to restart the service
restart_service() {
  echo "Restarting Cloud Run service..."
  gcloud run services update mobilize-crm --region us-central1 --no-traffic
  gcloud run services update mobilize-crm --region us-central1 --traffic=100
  echo "Cloud Run service restarted successfully!"
}

# Update environment variables only
if [ "$ENV_ONLY" = true ]; then
  echo "Updating environment variables..."
  gcloud run services update mobilize-crm \
    --region us-central1 \
    --update-env-vars "$ENV_VARS"
  echo "Environment variables updated successfully!"
  exit 0
fi

# Update secrets only
if [ "$SECRETS_ONLY" = true ]; then
  echo "Updating secrets..."
  gcloud run services update mobilize-crm \
    --region us-central1 \
    --update-secrets="$SECRETS"
  echo "Secrets updated successfully!"
  exit 0
fi

# Restart service only
if [ "$RESTART_ONLY" = true ]; then
  restart_service
  exit 0
fi

# Full deployment
echo "Performing full deployment..."

if [ "$SAFE_DEPLOY" = true ]; then
  # Safe deployment - deploy without sending traffic
  echo "Performing safe deployment (no immediate traffic)..."
  
  gcloud run deploy mobilize-crm \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --update-env-vars "$ENV_VARS" \
    --update-secrets="$SECRETS" \
    --cpu=1 \
    --memory=512Mi \
    --min-instances=1 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300s \
    --session-affinity \
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
else
  # Standard deployment
  gcloud run deploy mobilize-crm \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --update-env-vars "$ENV_VARS" \
    --update-secrets="$SECRETS" \
    --cpu=1 \
    --memory=512Mi \
    --min-instances=1 \
    --max-instances=10 \
    --concurrency=80 \
    --timeout=300s \
    --session-affinity
fi

echo "Deployment complete!"

# Check for errors after deployment
echo "Checking for errors in logs..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 5 --freshness=1m

echo "
IMPORTANT: Make sure to update your Google OAuth configuration in Google Cloud Console:"
echo "1. Go to Google Cloud Console > APIs & Services > Credentials"
echo "2. Edit your OAuth 2.0 Client ID"
echo "3. Add both https://mobilize-crm.org/api/auth/google/callback and https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback to the Authorized Redirect URIs"
echo "
ALSO: Update Firebase Authentication:"
echo "1. Go to Firebase Console > Authentication > Settings > Authorized Domains"
echo "2. Add mobilize-crm.org to the list of authorized domains"
