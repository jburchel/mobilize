#!/bin/bash

# Script to update OAuth environment variables during deployment

echo "Updating OAuth environment variables for deployment..."

# Extract credentials from local .env.production file
GOOGLE_CLIENT_ID=$(grep GOOGLE_CLIENT_ID .env.production | cut -d= -f2)
GOOGLE_CLIENT_SECRET=$(grep GOOGLE_CLIENT_SECRET .env.production | cut -d= -f2)
BASE_URL="https://mobilize-app.onrender.com"

# Check if credentials were extracted successfully
if [ -z "$GOOGLE_CLIENT_ID" ] || [ -z "$GOOGLE_CLIENT_SECRET" ]; then
  echo "Error: Could not extract Google OAuth credentials from .env.production"
  exit 1
fi

echo "Setting environment variables for deployment..."

# For Render.com deployment
if [ -n "$RENDER" ]; then
  echo "Detected Render.com environment"
  # These variables should be set in the Render dashboard
  echo "Please make sure the following environment variables are set in your Render dashboard:"
  echo "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID"
  echo "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET"
  echo "BASE_URL=$BASE_URL"
fi

echo "OAuth environment variables updated successfully."
echo ""
echo "IMPORTANT: Make sure to add the following redirect URI to your Google Cloud Console:"
echo "$BASE_URL/api/auth/google/callback"
echo ""
echo "Follow these steps:"
echo "1. Go to https://console.cloud.google.com/apis/credentials"
echo "2. Find and edit your OAuth 2.0 Client ID"
echo "3. Add the above URL to the 'Authorized redirect URIs' section"
echo "4. Click Save"
