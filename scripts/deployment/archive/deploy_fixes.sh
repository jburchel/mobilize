#!/bin/bash

set -e

echo "Deploying OAuth fixes to Cloud Run..."

# This deployment includes fixes for Google OAuth authentication and session management:
# 1. Updated ngrok_fix.py to properly handle the custom domain mobilize-crm.org
# 2. Ensure OAuth redirect URIs are properly configured
# 3. Added session_fix.py to fix DetachedInstanceError issues
# 4. Enhanced db_transaction_fix.py for better error handling

# Build and deploy the application
gcloud run deploy mobilize-crm \
    --source . \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated

echo "Deployment complete!"
echo "
IMPORTANT: Make sure to update your Google OAuth configuration in Google Cloud Console:"
echo "1. Go to Google Cloud Console > APIs & Services > Credentials"
echo "2. Edit your OAuth 2.0 Client ID"
echo "3. Add both https://mobilize-crm.org/api/auth/google/callback and https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback to the Authorized Redirect URIs"
echo "
ALSO: Update Firebase Authentication:"
echo "1. Go to Firebase Console > Authentication > Settings > Authorized Domains"
echo "2. Add mobilize-crm.org to the list of authorized domains"
