#!/usr/bin/env python
"""
Script to list all users and check if they have person_id values.
"""
from app import create_app, db
from app.models.user import User

app = create_app()

def list_users():
    """List all users and check if they have person_id values."""
    with app.app_context():
        users = User.query.all()
        print(f"Found {len(users)} users:")
        for user in users:
            office_id = user.office_id or "None"
            person_id = user.person_id or "None"
            print(f"User {user.id}: {user.username}, {user.email}, office_id={office_id}, person_id={person_id}")

if __name__ == "__main__":
    list_users() 