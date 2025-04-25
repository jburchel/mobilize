# Setting Up Continuous Deployment with Cloud Build

Follow these steps to connect your GitHub repository to Google Cloud Build for continuous deployment:

## 1. Connect GitHub Repository to Cloud Build

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Make sure the "mobilize-crm" project is selected
3. Navigate to Cloud Build > Triggers
4. Click "Connect Repository"
5. Select GitHub as your source
6. Click "Continue" and authenticate with your GitHub account
7. Select your organization and repository (mobilize-app)
8. Click "Connect"

## 2. Create a Build Trigger

1. After connecting the repository, click "Create a Trigger"
2. Configure the trigger:
   - Name: `mobilize-crm-trigger`
   - Description: `Deploy Mobilize CRM to Cloud Run`
   - Event: Push to a branch
   - Source: Your connected repository
   - Branch: `^main$` (or your primary branch name)
   - Build configuration: Cloud Build configuration file (YAML)
   - Location: Repository
   - Cloud Build configuration file location: `cloudbuild.yaml`
3. Click "Create"

## 3. Verify Configuration

After creating the trigger, run the following command to verify it's been created:

```bash
gcloud builds triggers list
```

You should see your new trigger listed.

## 4. Test the Trigger

To test the trigger without pushing to your main branch, you can:

1. In the Cloud Build > Triggers page, find your trigger
2. Click the three-dot menu (⋮) on the right
3. Select "Run Trigger"
4. Select the branch to build from (can be main or another branch)
5. Click "Run"

You can monitor the build status in the Cloud Build > History page.

## 5. Ongoing Deployment

After setup, any push to your main branch will automatically:
1. Build a new Docker image
2. Push it to Container Registry
3. Deploy it to Cloud Run

You can verify successful deployments in the Cloud Run console. 