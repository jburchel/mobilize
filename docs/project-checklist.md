# Mobilize CRM Development and Testing Checklist

## Phase 1: Project Setup and Infrastructure

### Phase 1: Development Steps

- [ ] 1. Initialize Project Structure
  - [ ] Create project directory structure
  - [ ] Set up virtual environment
  - [ ] Create requirements.txt with initial dependencies
  - [ ] Initialize Git repository
  - [ ] Create .gitignore file
  - [ ] Set up GitHub project board
  - [ ] Configure issue templates

- [ ] 2. Environment Configuration
  - [ ] Create .env.development file
  - [ ] Create .env.production file
  - [ ] Set up environment variable loading
  - [ ] Configure logging

- [ ] 3. Database Setup
  - [ ] Set up local SQLite database for development
  - [ ] Create initial database migration scripts
  - [ ] Set up Supabase for production
  - [ ] Configure database connection handling
  - [ ] Update schema for multi-office structure
    - [ ] Create Office model and relationships
    - [ ] Add office associations to existing models
    - [ ] Implement data ownership and visibility rules
    - [ ] Create migration scripts for new structure

- [ ] 4. Authentication Setup
  - [ ] Configure Firebase Authentication
  - [ ] Set up Google OAuth2
  - [ ] Update role-based access control
    - [ ] Implement Super Admin role
    - [ ] Implement Office Admin role
    - [ ] Add office context to user sessions
    - [ ] Create permission middleware
  - [ ] Create user session management

### Phase 1 Testing Milestones

- [ ] 1. Infrastructure Verification
  - [ ] Run basic Flask application
  - [ ] Verify environment variables are loading correctly
  - [ ] Confirm logging is working
  - [ ] Test database connections

- [ ] 2. Authentication Testing
  - [ ] Test Google OAuth login flow
  - [ ] Verify user session creation
  - [ ] Test role-based access
  - [ ] Confirm logout functionality

- [ ] 3. Office Structure Testing
  - [ ] Test office isolation
  - [ ] Verify user-office associations
  - [ ] Test role-based permissions
  - [ ] Validate data visibility rules

Phase 1 Complete when: Application runs locally with working authentication and database connection

## Phase 2: Core Backend Development

### Phase 2: Development Steps

- [ ] 1. Models Implementation
  - [ ] Design and implement User model
  - [ ] Update User model with office relations
  - [ ] Create Person (Contact) model
  - [ ] Update Person model with ownership rules
  - [ ] Develop Task model
  - [ ] Update Task model for shared tasks
  - [ ] Implement Communication model
  - [ ] Update Communication model with office context
  - [ ] Set up model relationships
  - [ ] Implement Office model and relationships

- [ ] 2. API Development
  - [ ] Create Authentication endpoints
  - [ ] Update auth endpoints for office context
  - [ ] Implement Contacts API
  - [ ] Update Contacts API with visibility rules
  - [ ] Develop Tasks API
  - [ ] Update Tasks API for shared tasks
  - [ ] Create Communications API
  - [ ] Update Communications API with office context
  - [ ] Implement Office management API
  - [ ] Create User management endpoints
  - [ ] Add office management endpoints

- [ ] 3. Google Services Integration
  - [ ] Gmail API integration
  - [ ] Calendar API integration
  - [ ] Google Contacts Integration
    - [ ] Configure Google People API access
    - [ ] Create contact mapping system
    - [ ] Handle contact deduplication
    - [ ] Implement periodic sync for contact updates
    - [ ] Add contact import history tracking
    - [ ] Implement contact selection interface
    - [ ] Create contact merge resolution system
  - [ ] Background jobs for synchronization

### Phase 2 Testing Milestones

- [ ] 1. Model Testing
  - [ ] Create test data in database
  - [ ] Verify relationships between models
  - [ ] Test CRUD operations for each model
  - [ ] Confirm data integrity constraints

- [ ] 2. API Testing
  - [ ] Test each API endpoint using Postman/curl
  - [ ] Verify authentication requirements
  - [ ] Test error handling
  - [ ] Confirm data validation

- [ ] 3. Integration Testing
  - [ ] Test Gmail synchronization
  - [ ] Verify Calendar integration
  - [ ] Google Contacts Testing
    - [ ] Test contact selection and import
    - [ ] Verify contact mapping accuracy
    - [ ] Test deduplication logic
    - [ ] Verify periodic sync functionality
    - [ ] Test merge conflict resolution
  - [ ] Confirm background jobs are running

Phase 2 Complete when: All APIs return expected responses and Google services are properly integrated

## Phase 3: Frontend Development

### Phase 3: Development Steps

- [ ] 1. Base Template and Layout
  - [ ] Create base template with navigation
  - [ ] Implement responsive sidebar
    - [ ] Add utility section divider
    - [ ] Add Admin section
    - [ ] Add Google Sync section
    - [ ] Add Settings section
  - [ ] Set up header component
  - [ ] Configure static assets

- [ ] 2. Core Pages Development
  - [ ] Build Dashboard view
  - [ ] Create Office Management Interface
    - [ ] Office creation and management
    - [ ] User role assignment
    - [ ] Permission management
    - [ ] Office-specific settings
  - [ ] Create People management interface
  - [ ] Develop Churches management interface
  - [ ] Build Communications hub
  - [ ] Create Task management interface
  - [ ] Implement Google Integration Interface
    - [ ] Create Google Sync dashboard
    - [ ] Build contact import wizard
    - [ ] Add sync status indicators
    - [ ] Create sync history view
    - [ ] Implement conflict resolution interface
    - [ ] Add manual sync triggers
    - [ ] Create contact mapping interface

- [ ] 3. UI Components
  - [ ] Implement form components
  - [ ] Create data table components
  - [ ] Build modal dialogs
  - [ ] Develop notification system
  - [ ] Create Google-specific Components
    - [ ] Contact selector component
    - [ ] Sync status indicator
    - [ ] Contact merge resolver
    - [ ] Import progress tracker

### Phase 3 Testing Milestones

- [ ] 1. Layout Testing
  - [ ] Verify responsive design on multiple devices
  - [ ] Test navigation functionality
  - [ ] Check component styling matches design
  - [ ] Confirm proper asset loading

- [ ] 2. Page Functionality Testing
  - [ ] Test all CRUD operations through UI
  - [ ] Verify data display and updates
  - [ ] Test form submissions
  - [ ] Check error handling and user feedback
  - Note: Tests have been set up with both mock mode and real browser mode (via USE_REAL_BROWSER=true)
  - Note: Testing framework supports Chrome, Firefox, and Microsoft Edge browsers

- [ ] 3. UI Component Testing
  - [ ] Test all interactive components
  - [ ] Verify modal functionality
  - [ ] Test notification system
  - [ ] Check form validation

Phase 3 Complete when: All pages are functional and responsive with working UI components

## Phase 4: Advanced Features

### Phase 4: Development Steps

- [ ] 1. Pipeline Management
  - [ ] Create pipeline visualization
  - [ ] Implement stage transitions
  - [ ] Set up automation rules

- [ ] 2. Reporting System
  - [ ] Create dashboard widgets
  - [ ] Implement data export
  - [ ] Build custom report generator

- [ ] 3. Email Integration
  - [ ] Template management system
  - [ ] Email tracking
  - [ ] Bulk email capabilities

- [ ] 4. Task Automation
  - [ ] Set up scheduled tasks
  - [ ] Configure email notifications
  - [ ] Implement reminder system

### Phase 4 Testing Milestones

- [ ] 1. Pipeline Testing
  - [ ] Test contact movement through pipeline
  - [ ] Verify automation rules
  - [ ] Check pipeline visualization

- [ ] 2. Reporting Testing
  - [ ] Verify dashboard data accuracy
  - [ ] Test export functionality
  - [ ] Validate custom reports

- [ ] 3. Email System Testing
  - [ ] Test template creation and usage
  - [ ] Verify email tracking
  - [ ] Test bulk email functionality

- [ ] 4. Task Automation
  - [ ] Set up scheduled tasks
  - [ ] Configure email notifications
  - [ ] Implement reminder system

Phase 4 Complete when: All advanced features are working reliably

## Phase 5: Quality Assurance and Performance

### Phase 5: Development Steps

- [ ] 1. Performance Optimization
  - [ ] Optimize database queries
  - [ ] Implement caching
  - [ ] Minimize API calls
  - [ ] SQLAlchemy 2.0 Migration
    - [ ] Update model definitions with type hints
    - [ ] Resolve relationship definition warnings
    - [ ] Implement 2.0-style queries
    - [ ] Update transaction management patterns

- [ ] 2. Security Implementation
  - [ ] Implement CSRF protection
  - [ ] Set up XSS prevention
  - [ ] Configure rate limiting
  - [ ] Set up branch protection rules
  - [ ] Configure security scanning

### Phase 5 Testing Milestones

- [ ] 1. Performance Testing
  - [ ] Run load tests
  - [ ] Measure page load times
  - [ ] Test with large datasets
  - [ ] Verify caching effectiveness

- [ ] 2. Security Testing
  - [ ] Perform security audit
  - [ ] Test all security measures
  - [ ] Verify data protection
  - [ ] Check access controls

Phase 5 Complete when: Application performs well under load and passes security tests

## Phase 6: Deployment and Documentation

### Phase 6: Development Steps

- [ ] 1. Deployment Setup
  - [ ] Configure Google Cloud Run
  - [ ] Set up Supabase production database
  - [ ] Configure production environment
  - [ ] Set up CI/CD pipeline
  - [ ] Configure automated testing
  - [ ] Set up automated deployments

- [ ] 2. Documentation
  - [ ] Create API documentation
  - [ ] Write user manual
  - [ ] Document deployment procedures

### Phase 6 Testing Milestones

- [ ] 1. Deployment Testing
  - [ ] Test production environment
  - [ ] Verify all features in production
  - [ ] Test backup procedures
  - [ ] Verify monitoring systems

- [ ] 2. Documentation Testing
  - [ ] Verify API documentation accuracy
  - [ ] Test user manual procedures
  - [ ] Validate deployment instructions

Phase 6 Complete when: Application is deployed and fully documented

## Phase 7: Post-Launch

### Phase 7: Steps and Testing

- [ ] 1. User Acceptance Testing
  - [ ] Gather user feedback
  - [ ] Address user-reported issues
  - [ ] Make necessary adjustments

- [ ] 2. Performance Monitoring
  - [ ] Monitor application metrics
  - [ ] Track error rates
  - [ ] Measure user engagement

- [ ] 3. Continuous Improvement
  - [ ] Implement user suggestions
  - [ ] Optimize based on metrics
  - [ ] Plan future enhancements

Phase 7 Complete when: Application is stable and users are satisfied

## Project Checklist for Mobilize-CRM

## Phase 1: Initial Diagnosis and Setup

- [ ] Review error logs to identify the cause of 'Service Unavailable' on dashboard
- [ ] Set up environment and verify configuration settings
- [ ] Create or update error handling to capture detailed logs

## Phase 2: Data Integrity Fixes

- [ ] Develop script to fix `office_id` data type mismatches in database tables
- [ ] Execute `fix_office_id_data.py` script to convert string `office_id` values to integers
- [ ] Handle schema mismatches by checking for column existence before updates

## Phase 3: Database Schema Alignment

- [ ] Investigate discrepancies between database schema and SQLAlchemy model definitions
- [ ] Update database schema or models to resolve missing column errors (e.g., `contacts.church_name`, `tasks.reminder_time`)
- [ ] Apply necessary migrations to align database structure with application expectations

## Phase 4: Redeployment and Validation

- [ ] Commit and push changes to trigger deployment to Google Cloud Run
- [ ] Verify resolution of 'Service Unavailable' error on dashboard
- [ ] Monitor logs for any residual or new issues post-deployment
- [ ] Resolve app initialization issues to enable database schema inspection
- [ ] Address SQLAlchemy warnings about implicit column combinations

**Note**: A branch `revert_to_pre_chat_state` has been created and pushed to the repository, representing the codebase before the changes made in the recent chat session. See `revert_instructions.md` for details on using this branch to revert to the pre-chat state.

## Phase 5: Cleanup and Optimization

- [ ] Remove or archive deprecated files and scripts
- [ ] Document all fixes and procedures for future reference
- [ ] Review and refine SQLAlchemy models to eliminate warnings

**Note**: Ensure each phase is completed before moving to the next. Refer to `mobilize-prompt.md` for detailed project context if needed.