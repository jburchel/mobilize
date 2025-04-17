# CI/CD Setup Guide for Mobilize CRM

This document provides instructions for setting up continuous integration and continuous deployment (CI/CD) for the Mobilize CRM application.

## GitHub Actions CI/CD Setup

### Prerequisites

- GitHub repository containing the Mobilize CRM codebase
- Google Cloud Platform (GCP) account with appropriate permissions
- GCP project set up for deployment

### 1. Create a Service Account in GCP

Create a service account in GCP that will be used by GitHub Actions to deploy your application:

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
    --display-name="GitHub Actions Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding [YOUR-PROJECT-ID] \
    --member="serviceAccount:github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding [YOUR-PROJECT-ID] \
    --member="serviceAccount:github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding [YOUR-PROJECT-ID] \
    --member="serviceAccount:github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding [YOUR-PROJECT-ID] \
    --member="serviceAccount:github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Allow service account to act as service agent
gcloud iam service-accounts add-iam-policy-binding \
    [PROJECT-NUMBER]-compute@developer.gserviceaccount.com \
    --member="serviceAccount:github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

### 2. Create and Download a Service Account Key

```bash
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions-sa@[YOUR-PROJECT-ID].iam.gserviceaccount.com
```

### 3. Set Up GitHub Secrets

1. Go to your GitHub repository
2. Navigate to "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: The entire content of the `key.json` file you just created (base64 encoded)
   - `DB_PASSWORD`: Your Supabase PostgreSQL database password
   - `FLASK_SECRET_KEY`: A secure secret key for Flask

To encode your service account key:
```bash
cat key.json | base64
```

### 4. Create GitHub Actions Workflow Files

Create a file at `.github/workflows/ci-cd.yml` in your repository:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
        
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  deploy:
    name: Deploy to Google Cloud Run
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - id: 'auth'
      name: 'Authenticate to Google Cloud'
      uses: 'google-github-actions/auth@v1'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Build and push container
      run: |
        gcloud auth configure-docker
        docker build -t gcr.io/${{ secrets.GCP_PROJECT_ID }}/mobilize-crm:${{ github.sha }} .
        docker push gcr.io/${{ secrets.GCP_PROJECT_ID }}/mobilize-crm:${{ github.sha }}
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy mobilize-crm \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/mobilize-crm:${{ github.sha }} \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated \
          --set-secrets=DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest
    
    - name: Show deployed service URL
      run: |
        gcloud run services describe mobilize-crm --platform managed --region us-central1 --format 'value(status.url)'
```

### 5. Create a Separate Workflow for Database Migrations

Create a file at `.github/workflows/db-migrate.yml` in your repository:

```yaml
name: Database Migrations

on:
  workflow_run:
    workflows: ["CI/CD Pipeline"]
    types:
      - completed
    branches: [main]

jobs:
  migrate:
    name: Run Database Migrations
    if: ${{ github.event.workflow_run.conclusion == 'success' }}
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - id: 'auth'
      name: 'Authenticate to Google Cloud'
      uses: 'google-github-actions/auth@v1'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'
    
    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Run migrations
      run: |
        gcloud run jobs create db-migrate-${{ github.sha }} \
          --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/mobilize-crm:${{ github.sha }} \
          --region us-central1 \
          --set-secrets=DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest \
          --command "flask" \
          --args "db,upgrade"
        
        gcloud run jobs execute db-migrate-${{ github.sha }} \
          --region us-central1 \
          --wait
```

## GitLab CI/CD Setup (Alternative)

If you're using GitLab instead of GitHub, create a `.gitlab-ci.yml` file:

```yaml
image: docker:20.10.16

services:
  - docker:20.10.16-dind

stages:
  - test
  - build
  - deploy
  - migrate

variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_CERTDIR: "/certs"
  DOCKER_TLS_VERIFY: 1
  DOCKER_CERT_PATH: "$DOCKER_TLS_CERTDIR/client"

before_script:
  - echo $GCP_SA_KEY > /tmp/gcp-key.json
  - export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json

test:
  stage: test
  image: python:3.10
  script:
    - pip install -r requirements.txt
    - pip install pytest pytest-cov
    - pytest --cov=./ --cov-report=xml
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  only:
    - main
  script:
    - docker build -t gcr.io/$GCP_PROJECT_ID/mobilize-crm:$CI_COMMIT_SHA .
    - echo $GCP_SA_KEY | docker login -u _json_key --password-stdin https://gcr.io
    - docker push gcr.io/$GCP_PROJECT_ID/mobilize-crm:$CI_COMMIT_SHA
  dependencies:
    - test

deploy:
  stage: deploy
  image: google/cloud-sdk:alpine
  only:
    - main
  script:
    - gcloud auth activate-service-account --key-file /tmp/gcp-key.json
    - gcloud config set project $GCP_PROJECT_ID
    - gcloud run deploy mobilize-crm --image gcr.io/$GCP_PROJECT_ID/mobilize-crm:$CI_COMMIT_SHA --platform managed --region us-central1 --allow-unauthenticated --set-secrets=DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest
  dependencies:
    - build

migrate:
  stage: migrate
  image: google/cloud-sdk:alpine
  only:
    - main
  script:
    - gcloud auth activate-service-account --key-file /tmp/gcp-key.json
    - gcloud config set project $GCP_PROJECT_ID
    - gcloud run jobs create db-migrate-$CI_COMMIT_SHORT_SHA --image gcr.io/$GCP_PROJECT_ID/mobilize-crm:$CI_COMMIT_SHA --region us-central1 --set-secrets=DATABASE_URL=mobilize-db-url:latest,SECRET_KEY=mobilize-flask-secret:latest --command "flask" --args "db,upgrade"
    - gcloud run jobs execute db-migrate-$CI_COMMIT_SHORT_SHA --region us-central1 --wait
  dependencies:
    - deploy
```

## Configuring Branch Protection Rules

To ensure code quality and prevent breaking changes:

1. Go to your GitHub repository
2. Navigate to "Settings" > "Branches"
3. Click "Add rule" under "Branch protection rules"
4. Set up the following rules for your main branch:
   - Require pull request reviews before merging
   - Require status checks to pass before merging
   - Select the "test" workflow as a required status check
   - Require branches to be up to date before merging

## Monitoring Deployments

### GitHub Actions

1. Go to your GitHub repository
2. Navigate to "Actions" tab
3. You can see all workflow runs and their status

### Google Cloud Console

1. Go to Google Cloud Console
2. Navigate to "Cloud Run" to see the deployed services
3. Navigate to "Cloud Build" > "History" to see the build history

## Troubleshooting CI/CD Issues

### Failed Tests

If tests are failing:

1. Check the test output in the GitHub Actions logs
2. Fix the failing tests locally
3. Push the changes and ensure tests pass before merging

### Deployment Failures

If deployment fails:

1. Check the workflow logs in GitHub Actions
2. Common issues include:
   - Invalid service account permissions
   - Image build failures
   - Cloud Run deployment errors

3. Verify that all required secrets are properly set in GitHub repository settings

## Best Practices

1. Always write tests for new features
2. Keep sensitive information in GitHub Secrets, not in the code
3. Use separate environments for development, staging, and production
4. Tag releases with semantic versioning
5. Use feature branches and pull requests for all changes
6. Review deployment logs regularly
7. Set up monitoring and alerting for production deployments 