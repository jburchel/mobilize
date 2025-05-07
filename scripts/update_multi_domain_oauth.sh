#!/bin/bash

# Script to update OAuth configuration for multiple domains

echo "======================================================="
echo "Google OAuth Multiple Domain Configuration"
echo "======================================================="

# Get the current Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe mobilize-crm --region=us-central1 --format="value(status.url)")
CUSTOM_DOMAIN="https://mobilize-crm.org"

echo "Your application is accessible at two URLs:"
echo "1. Cloud Run URL: $CLOUD_RUN_URL"
echo "2. Custom Domain: $CUSTOM_DOMAIN"
echo ""

echo "You need to add BOTH of these redirect URIs to your Google Cloud Console:"
echo "$CLOUD_RUN_URL/api/auth/google/callback"
echo "$CUSTOM_DOMAIN/api/auth/google/callback"
echo ""

echo "Follow these steps:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Find and edit your OAuth 2.0 Client ID"
echo "3. Add BOTH URLs to the 'Authorized redirect URIs' section"
echo "4. Click Save"
echo ""

echo "Would you like to update the BASE_URL environment variable to use your custom domain? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Updating BASE_URL in Cloud Run to use custom domain..."
    gcloud run services update mobilize-crm \
        --region=us-central1 \
        --update-env-vars="BASE_URL=$CUSTOM_DOMAIN"
    echo "BASE_URL updated successfully to $CUSTOM_DOMAIN!"
else
    echo "Skipping BASE_URL update. You'll need to do this manually if needed."
fi

echo ""
echo "After making these changes, your OAuth authentication should work correctly on both domains."
echo "======================================================="
