#!/bin/bash

# Script to set environment variables on Google Cloud Run

echo "Setting environment variables on Google Cloud Run..."

# Set variables
SERVICE_NAME="mobilize-crm"
REGION="us-central1"
PROJECT_ID="mobilize-crm"

# Get the OAuth credentials from .env.production
GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID .env.production | cut -d= -f2)
GOOGLE_CLIENT_SECRET=$(grep GOOGLE_CLIENT_SECRET .env.production | cut -d= -f2)
BASE_URL=$(grep BASE_URL .env.production | cut -d= -f2)

# Check if credentials were extracted successfully
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ] || [ -z "$BASE_URL" ]; then
  echo "Error: Could not extract OAuth credentials from .env.production"
  exit 1
fi

echo "Setting environment variables for $SERVICE_NAME in $REGION..."

# Update Cloud Run service with environment variables
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --update-env-vars="GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID,GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET,BASE_URL=$BASE_URL"

echo "\nEnvironment variables set successfully!"
echo "\nIMPORTANT: Make sure to add the following redirect URI to your Google Cloud Console:"
echo "$BASE_URL/api/auth/google/callback"
echo "\nFollow these steps:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Find and edit your OAuth 2.0 Client ID"
echo "3. Add the above URL to the 'Authorized redirect URIs' section"
echo "4. Click Save"
