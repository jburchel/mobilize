#!/usr/bin/env python3
"""
Script to compare query performance between SQLite and PostgreSQL databases
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

def test_sqlite_performance():
    """Test query performance on SQLite database"""
    print("\n=== TESTING SQLITE PERFORMANCE ===")
    
    # Set environment to development for SQLite
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_APP'] = 'app.py'
    
    # Clear any existing imports
    if 'app' in sys.modules:
        del sys.modules['app']
    if 'app.models.user' in sys.modules:
        del sys.modules['app.models.user']
    
    # Import app context and models after environment is set
    from app import create_app
    from app.models.user import User
    from app.models.office import Office
    from app.models.task import Task
    
    app = create_app()
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        # Warm up the connection
        User.query.first()
        
        # Test simple query performance
        print("\nSimple Query: User.query.all()")
        start_time = time.time()
        users = User.query.all()
        end_time = time.time()
        print(f"Found {len(users)} users in {end_time - start_time:.4f} seconds")
        
        # Test join query performance
        print("\nJoin Query: Tasks with assignees")
        start_time = time.time()
        tasks = Task.query.join(User, Task.assignee_id == User.id).all()
        end_time = time.time()
        print(f"Found {len(tasks)} tasks with assignees in {end_time - start_time:.4f} seconds")
        
        # Test complex query performance
        print("\nComplex Query: Users with offices and tasks")
        start_time = time.time()
        results = User.query.join(Office, User.office_id == Office.id).all()
        end_time = time.time()
        print(f"Found {len(results)} users with offices in {end_time - start_time:.4f} seconds")
    
    return True

def test_postgres_performance():
    """Test query performance on PostgreSQL database"""
    print("\n=== TESTING POSTGRESQL PERFORMANCE ===")
    
    # Set environment to production for PostgreSQL
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_APP'] = 'app.py'
    
    # Clear any existing imports
    if 'app' in sys.modules:
        del sys.modules['app']
    if 'app.models.user' in sys.modules:
        del sys.modules['app.models.user']
    
    # Import app context and models after environment is set
    from app import create_app
    from app.models.user import User
    from app.models.office import Office
    from app.models.task import Task
    
    app = create_app()
    print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        # Warm up the connection
        User.query.first()
        
        # Test simple query performance
        print("\nSimple Query: User.query.all()")
        start_time = time.time()
        users = User.query.all()
        end_time = time.time()
        print(f"Found {len(users)} users in {end_time - start_time:.4f} seconds")
        
        # Test join query performance
        print("\nJoin Query: Tasks with assignees")
        start_time = time.time()
        tasks = Task.query.join(User, Task.assignee_id == User.id).all()
        end_time = time.time()
        print(f"Found {len(tasks)} tasks with assignees in {end_time - start_time:.4f} seconds")
        
        # Test complex query performance
        print("\nComplex Query: Users with offices and tasks")
        start_time = time.time()
        results = User.query.join(Office, User.office_id == Office.id).all()
        end_time = time.time()
        print(f"Found {len(results)} users with offices in {end_time - start_time:.4f} seconds")
    
    return True

def main():
    print("Comparing SQLite and PostgreSQL performance...\n")
    
    # Test SQLite performance
    if not test_sqlite_performance():
        print("❌ SQLite performance tests failed")
    
    # Test PostgreSQL performance
    if not test_postgres_performance():
        print("❌ PostgreSQL performance tests failed")
    
    print("\n✅ Performance comparison completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 