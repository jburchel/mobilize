# Fresh Deployment Plan for Mobilize App

## Preparation Steps

1. **Backup Current Production Data**
   - Export any critical data from the production database
   - Document current environment variables and configurations

2. **Verify Local Development Environment**
   - Ensure local development version is working as expected
   - Run all tests to confirm functionality
   - Document all environment variables used in development

3. **Clean Up Repository**
   - Remove any unnecessary files or directories
   - Ensure all required files are committed
   - Create a clean branch for deployment

## Deployment Steps

1. **Set Up New Production Environment**
   - Create a new deployment environment in Cloud Run
   - Set up a new database instance if needed
   - Configure all environment variables to match development

2. **Disable Production Optimizations**
   - Modify `app/config/static_optimizations.py` to disable compression in production temporarily
   - Modify `app/config/frontend_optimizations.py` to disable optimizations temporarily
   - Add a flag to bypass environment-specific code paths

3. **Deploy the Application**
   - Push the clean branch to the repository
   - Trigger a new build and deployment
   - Monitor the deployment logs for any issues

4. **Verify Deployment**
   - Check all pages and functionality in the new production environment
   - Compare with local development to ensure they match
   - Test all features listed in DEBUG_CHECKLIST.md

5. **Gradually Re-enable Optimizations**
   - Once the base deployment is working, re-enable optimizations one by one
   - Test after each change to identify any problematic optimizations
   - Document which optimizations are safe to use

## Specific Code Changes

### 1. Disable Static File Optimizations

In `app/config/static_optimizations.py`:

```python
def optimize_static_files(app):
    """Apply optimizations for static file serving in production."""
    # Temporarily disable all optimizations
    app.logger.info("Static file optimizations disabled for fresh deployment")
    return
    
    # Original code below...
```

### 2. Disable Frontend Optimizations

In `app/config/frontend_optimizations.py`:

```python
def optimize_frontend_performance(app):
    """Apply frontend performance optimizations."""
    # Temporarily disable all optimizations
    app.logger.info("Frontend optimizations disabled for fresh deployment")
    return
    
    # Original code below...
```

### 3. Add Environment Flag

In `app/__init__.py`:

```python
# Add this near the top of create_app function
app.config['FRESH_DEPLOYMENT'] = True
app.logger.info("Running in FRESH_DEPLOYMENT mode - bypassing optimizations")
```

### 4. Ensure CSS is Properly Loaded

Add to `app/templates/base.html`:

```html
<!-- Force reload CSS for fresh deployment -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}?v={{ now.timestamp() }}">
```

## Rollback Plan

If the fresh deployment doesn't resolve the issues:

1. Revert to the previous production environment
2. Restore any backed-up data
3. Re-evaluate the differences between development and production
