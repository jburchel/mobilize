# SQLAlchemy 2.0 Migration Plan

## Overview
This document outlines the steps needed to migrate our codebase to SQLAlchemy 2.0 style queries and patterns.

## Changes Required

### 1. Model Updates
- Add type annotations to all model attributes
- Update relationship definitions to use 2.0 style
- Remove use of `Model.query` property

### 2. Query Pattern Updates
- Replace `db.session.query()` with `db.select()`
- Update filter patterns to use modern syntax
- Use `scalars()` for single-model queries
- Implement proper session handling

### 3. Migration Steps

#### Phase 1: Model Updates
1. Add SQLAlchemy type annotations
2. Update relationship definitions
3. Add proper foreign key constraints

#### Phase 2: Query Updates
1. Replace legacy query patterns
2. Update filter expressions
3. Implement proper session handling
4. Add proper error handling

#### Phase 3: Testing
1. Add comprehensive tests for new query patterns
2. Verify performance improvements
3. Load testing with larger datasets

## Files Needing Updates

### High Priority
- app/models/*.py (All model files)
- app/routes/api/v1/contacts.py
- app/routes/reports.py
- app/routes/pipeline.py
- app/controllers/pipeline_controller.py

### Medium Priority
- app/routes/emails.py
- app/routes/admin.py
- app/utils/*.py

### Low Priority
- scripts/*.py
- tests/*.py

## Example Migrations

### Legacy Pattern:
```python
users = User.query.filter_by(active=True).all()
```

### SQLAlchemy 2.0 Pattern:
```python
stmt = select(User).where(User.active == True)
users = db.session.execute(stmt).scalars().all()
```

## Performance Monitoring
- Add query timing metrics
- Monitor database load
- Track query patterns
- Implement query caching where appropriate 