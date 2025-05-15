# Google OAuth Configuration Fix

Follow these steps to fix the "Access blocked: Authorization Error" when clicking on "Sign in with Google":

## Update Google OAuth Client Configuration

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (mobilize-crm)
3. Navigate to "APIs & Services" > "Credentials"
4. Find your OAuth 2.0 Client ID and click on it to edit
5. Under "Authorized redirect URIs", add the following URIs if they're not already there:
   - `https://mobilize-crm.org/api/auth/google/callback`
   - `https://mobilize-crm-x3exfzl3zq-uc.a.run.app/api/auth/google/callback` (Cloud Run URL)
   - `https://mobilize-crm-1069318103780.us-central1.run.app/api/auth/google/callback` (Cloud Run URL)
6. Click "Save"

## Verify Environment Variables

Make sure the following environment variables are correctly set in your Cloud Run service:

1. `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
2. `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
3. `BASE_URL`: Set to `https://mobilize-crm.org`

You can verify these by checking the Cloud Run service configuration in the Google Cloud Console or by running:

```bash
gcloud run services describe mobilize-crm --region=us-central1 --format="yaml(spec.template.spec.containers[0].env)"
```

## Test the Fix

After making these changes, try signing in with Google again. The "Access blocked: Authorization Error" should be resolved.

## Additional Information

The error occurs because Google's OAuth service is strict about redirect URIs for security reasons. When a user authenticates, Google will only redirect to URIs that have been explicitly authorized in the OAuth client configuration.

In your application, the redirect URI is determined by the `get_oauth_redirect_uri()` function in `app/auth/google_oauth.py`, which tries to use the `BASE_URL` environment variable or falls back to other methods if it's not set.
