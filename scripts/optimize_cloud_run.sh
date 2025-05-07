#!/bin/bash

# Script to optimize Cloud Run configuration for better performance

echo "Optimizing Cloud Run configuration for better performance..."

# Set variables
SERVICE_NAME="mobilize-crm"
REGION="us-central1"
MIN_INSTANCES=1  # Prevent cold starts by keeping at least one instance warm
CPU="1"         # Allocate 1 full CPU (default is 0.25)
MEMORY="512Mi"   # Increase memory allocation
CONCURRENCY=80   # Maximum concurrent requests per instance

# Update Cloud Run service configuration
gcloud run services update $SERVICE_NAME \
  --region=$REGION \
  --min-instances=$MIN_INSTANCES \
  --cpu=$CPU \
  --memory=$MEMORY \
  --concurrency=$CONCURRENCY

echo "\nCloud Run optimization complete!"
echo "\nCurrent configuration:"
gcloud run services describe $SERVICE_NAME --region=$REGION --format="yaml(spec.template.spec.containers[0].resources,spec.template.spec.containerConcurrency,spec.template.metadata.annotations['autoscaling.knative.dev/minScale'])"
