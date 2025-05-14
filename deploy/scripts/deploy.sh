#!/bin/bash

set -e

# Mobilize CRM Deployment Script
# This script handles the deployment process for the Mobilize CRM application

echo "===== Deploying Mobilize CRM to Cloud Run ====="

# Parse command line arguments
SAFE_DEPLOY=false
DEPLOY_ONLY=false
ENV_ONLY=false
SECRETS_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --safe-deploy)
      SAFE_DEPLOY=true
      shift
      ;;
    --deploy-only)
      DEPLOY_ONLY=true
      shift
      ;;
    --env-only)
      ENV_ONLY=true
      shift
      ;;
    --secrets-only)
      SECRETS_ONLY=true
      shift
      ;;
    --help)
      echo "Usage: $0 [--safe-deploy] [--deploy-only] [--env-only] [--secrets-only]"
      echo "  --safe-deploy    Deploy without sending traffic immediately"
      echo "  --deploy-only    Deploy without updating environment variables or secrets"
      echo "  --env-only       Update only environment variables"
      echo "  --secrets-only   Update only secrets"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use --help for usage information"
      exit 1
      ;;
  esac
done

# Environment variables
ENV_VARS="FLASK_APP=app.py,FLASK_ENV=production,LOG_LEVEL=INFO,LOG_TO_STDOUT=True,PREFERRED_URL_SCHEME=https"

# Secrets
SECRETS="DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest,FIREBASE_CREDENTIALS=firebase-credentials:latest,GOOGLE_CLIENT_ID=mobilize-google-client-id:latest,GOOGLE_CLIENT_SECRET=mobilize-google-client-secret:latest"

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

# Deploy only (no env vars or secrets update)
if [ "$DEPLOY_ONLY" = true ]; then
  if [ "$SAFE_DEPLOY" = true ]; then
    # Safe deployment without traffic
    echo "Deploying without traffic..."
    gcloud run deploy mobilize-crm \
      --source . \
      --region us-central1 \
      --platform managed \
      --allow-unauthenticated \
      --cpu=1 \
      --memory=512Mi \
      --min-instances=1 \
      --max-instances=10 \
      --concurrency=80 \
      --timeout=300s \
      --no-traffic
      
    echo "Deployment complete. New revision is not receiving traffic."
    echo "To migrate traffic to the new revision, run:"
    echo "gcloud run services update-traffic mobilize-crm --region us-central1 --to-latest"
  else
    # Standard deployment
    echo "Deploying with immediate traffic..."
    gcloud run deploy mobilize-crm \
      --source . \
      --region us-central1 \
      --platform managed \
      --allow-unauthenticated \
      --cpu=1 \
      --memory=512Mi \
      --min-instances=1 \
      --max-instances=10 \
      --concurrency=80 \
      --timeout=300s
  fi
  exit 0
fi

# Full deployment (with env vars and secrets)
if [ "$SAFE_DEPLOY" = true ]; then
  # Safe deployment without traffic
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
  echo "Performing standard deployment (with immediate traffic)..."
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
    --timeout=300s
fi

echo "Deployment complete!"

# Check for errors after deployment
echo "Checking for errors in logs..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=mobilize-crm AND severity>=ERROR" --limit 5 --freshness=1m
