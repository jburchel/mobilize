#!/bin/bash
# Verify the Cloud Build trigger has been created

echo "Checking for Cloud Build triggers..."
gcloud builds triggers list

echo ""
echo "Verifying cloudbuild.yaml file..."
if [ -f cloudbuild.yaml ]; then
  echo "✅ cloudbuild.yaml file exists"
else
  echo "❌ cloudbuild.yaml file not found"
  exit 1
fi

echo ""
echo "Verifying Dockerfile..."
if [ -f Dockerfile ]; then
  echo "✅ Dockerfile exists"
else
  echo "❌ Dockerfile not found"
  exit 1
fi

echo ""
echo "Verifying Secret Manager secrets..."
REQUIRED_SECRETS=(
  "mobilize-db-url"
  "mobilize-flask-secret"
  "mobilize-google-client-id"
  "mobilize-google-client-secret"
)

for secret in "${REQUIRED_SECRETS[@]}"; do
  if gcloud secrets describe "$secret" &>/dev/null; then
    echo "✅ Secret $secret exists"
  else
    echo "❌ Secret $secret not found"
    exit 1
  fi
done

echo ""
echo "All verification checks passed. Your setup is ready for Continuous Deployment!"
echo "After connecting your GitHub repository and setting up the trigger in the Google Cloud Console,"
echo "any push to your main branch will automatically deploy to Cloud Run." 