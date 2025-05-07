#!/bin/bash

# Script to provide instructions for updating OAuth redirect URIs

echo "======================================================="
echo "Google OAuth Redirect URI Update Instructions"
echo "======================================================="

# Get the current Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe mobilize-crm --region=us-central1 --format="value(status.url)")

echo "Your Cloud Run application is deployed at:"
echo "$CLOUD_RUN_URL"
echo ""

echo "You need to add the following redirect URI to your Google Cloud Console:"
echo "$CLOUD_RUN_URL/api/auth/google/callback"
echo ""

echo "Follow these steps:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Find and edit your OAuth 2.0 Client ID"
echo "3. Add the above URL to the 'Authorized redirect URIs' section"
echo "4. Click Save"
echo ""

echo "Additionally, you need to update your environment variables in Cloud Run:"
echo "BASE_URL=$CLOUD_RUN_URL"
echo ""

echo "Would you like to update the BASE_URL environment variable in Cloud Run now? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Updating BASE_URL in Cloud Run..."
    gcloud run services update mobilize-crm \
        --region=us-central1 \
        --update-env-vars="BASE_URL=$CLOUD_RUN_URL"
    echo "BASE_URL updated successfully!"
else
    echo "Skipping BASE_URL update. You'll need to do this manually."
fi

echo ""
echo "After making these changes, your OAuth authentication should work correctly."
echo "======================================================="
