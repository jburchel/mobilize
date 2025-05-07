# Name Display Fix Documentation

## Problem Description

Users were experiencing an issue where names were displaying as "None None" on the people and church list pages. This occurred because:

1. The application uses a polymorphic inheritance model where:
   - `Contact` is the base class with `first_name` and `last_name` fields
   - `Person` inherits from `Contact` and also has its own `first_name` and `last_name` fields
   - `Church` inherits from `Contact` and has a `name` field

2. The issue was that data was being stored inconsistently:
   - For people: Data might be stored in the `people.first_name` and `people.last_name` columns, but not in the corresponding `contacts.first_name` and `contacts.last_name` columns
   - For churches: Data might be stored in the `churches.name` column, but not in the `contacts.first_name` column

3. The templates were directly accessing these fields, causing NULL values to be displayed as "None None".

## Solution

We implemented a three-part solution to fix this issue:

### 1. Template Fixes

We updated the templates to use the `get_name()` method instead of directly accessing the name fields:

- In `people/list.html`: Changed from `{{ person.first_name }} {{ person.last_name }}` to `{{ person.get_name() }}`
- In `churches/index.html`: Changed from `{{ church.name }}` to `{{ church.get_name() }}`

### 2. Model Enhancements

We enhanced the `get_name()` methods in both the `Person` and `Church` models to check both the model's own fields and the inherited fields from the `Contact` base class:

- In `Person.get_name()`: Now checks both `person.first_name`/`person.last_name` and `contact.first_name`/`contact.last_name`
- In `Church.get_name()`: Now checks both `church.name` and `contact.first_name`

This ensures that names are displayed correctly even if data is stored inconsistently between tables.

### 3. Database Synchronization Scripts

We created scripts to fix the data inconsistency issues in both development and production environments:

- `fix_contact_names.py`: For local SQLite database
- `fix_production_names.py`: For production PostgreSQL database

These scripts:
1. Synchronize name fields between the contacts table and the people/churches tables
2. Create database triggers (in production) to ensure that future updates to the people and churches tables will automatically update the corresponding contact records

## Diagnostic Tools

We also created a diagnostic script to help identify issues in the production database:

- `check_prod_db.py`: Connects to the production database and provides detailed information about the database structure and data

## How to Use

### For Development

```bash
# Run the fix script for the local database
python fix_contact_names.py
```

### For Production

```bash
# Check the production database for issues
python check_prod_db.py

# Fix the production database
python fix_production_names.py
```

## Future Considerations

1. **Data Validation**: Consider adding validation to ensure that name fields are properly populated when creating or updating records.

2. **ORM Configuration**: Review the SQLAlchemy ORM configuration to ensure that data is consistently stored in both the base and derived tables.

3. **Monitoring**: Set up monitoring to detect similar issues in the future, such as NULL values in critical fields.
