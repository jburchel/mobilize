#!/usr/bin/env python
"""
Large Dataset Performance Test Script
Generates a large dataset and measures application performance
"""

import os
import time
import random
import logging
import argparse
import statistics
from tqdm import tqdm
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("large_dataset_test")

def generate_test_data(app, db, num_people=1000, num_churches=200):
    """Generate large test dataset"""
    from app.models.person import Person
    from app.models.church import Church
    from app.models.user import User
    from app.models.office import Office
    from app.models.task import Task
    from app.models.communication import Communication
    from app.utils.sample_data import (
        generate_sample_name, generate_sample_email, 
        generate_sample_address, generate_sample_phone
    )
    
    logger.info(f"Generating large test dataset: {num_people} people, {num_churches} churches")
    
    # Get the first office for testing
    office = Office.query.first()
    if not office:
        logger.error("No office found in database. Cannot generate test data.")
        return False
    
    # Get an admin user for associations
    admin_user = User.query.filter_by(role='admin').first()
    if not admin_user:
        logger.error("No admin user found. Cannot generate test data.")
        return False
    
    try:
        # Generate churches
        logger.info(f"Generating {num_churches} churches...")
        churches = []
        for i in tqdm(range(num_churches)):
            church = Church(
                name=f"Test Church {i+1}",
                address=generate_sample_address(),
                phone=generate_sample_phone(),
                email=f"church{i+1}@example.com",
                website=f"https://church{i+1}.example.com",
                office_id=office.id,
                created_by=admin_user.id
            )
            db.session.add(church)
            if i % 100 == 0:  # Commit in batches to avoid memory issues
                db.session.commit()
            churches.append(church)
        
        db.session.commit()
        logger.info("Churches created successfully")
        
        # Generate people
        logger.info(f"Generating {num_people} people...")
        people = []
        for i in tqdm(range(num_people)):
            first_name, last_name = generate_sample_name()
            person = Person(
                first_name=first_name,
                last_name=last_name,
                email=generate_sample_email(first_name, last_name),
                phone=generate_sample_phone(),
                address=generate_sample_address(),
                office_id=office.id,
                created_by=admin_user.id
            )
            
            # Randomly associate with a church
            if random.random() < 0.8:  # 80% of people are associated with a church
                church = random.choice(churches)
                person.churches.append(church)
            
            db.session.add(person)
            if i % 100 == 0:  # Commit in batches
                db.session.commit()
            people.append(person)
        
        db.session.commit()
        logger.info("People created successfully")
        
        # Generate tasks
        logger.info("Generating tasks...")
        for i in tqdm(range(num_people // 2)):  # Half the number of people
            person = random.choice(people)
            due_date = datetime.now() + timedelta(days=random.randint(1, 30))
            task = Task(
                title=f"Task for {person.first_name} {person.last_name}",
                description=f"Sample task description {i+1}",
                due_date=due_date,
                status=random.choice(['pending', 'in_progress', 'completed']),
                priority=random.choice(['low', 'medium', 'high']),
                assigned_to=admin_user.id,
                office_id=office.id,
                created_by=admin_user.id
            )
            
            # Associate with a person
            task.person_id = person.id
            
            db.session.add(task)
            if i % 100 == 0:
                db.session.commit()
        
        db.session.commit()
        logger.info("Tasks created successfully")
        
        # Generate communications
        logger.info("Generating communications...")
        for i in tqdm(range(num_people // 3)):  # One third the number of people
            person = random.choice(people)
            comm_date = datetime.now() - timedelta(days=random.randint(1, 60))
            communication = Communication(
                type=random.choice(['email', 'phone', 'meeting', 'other']),
                subject=f"Communication with {person.first_name} {person.last_name}",
                content=f"Sample communication content {i+1}",
                date=comm_date,
                person_id=person.id,
                user_id=admin_user.id,
                office_id=office.id
            )
            
            db.session.add(communication)
            if i % 100 == 0:
                db.session.commit()
        
        db.session.commit()
        logger.info("Communications created successfully")
        
        return True
    
    except Exception as e:
        logger.error(f"Error generating test data: {str(e)}")
        db.session.rollback()
        return False

def test_query_performance(app, db):
    """Test query performance with the large dataset"""
    from app.models.person import Person
    from app.models.church import Church
    from app.models.task import Task
    from app.models.communication import Communication
    from sqlalchemy import func, text
    
    logger.info("Testing query performance...")
    
    queries = [
        {
            "name": "Count all people",
            "query": lambda: db.session.query(func.count(Person.id)).scalar()
        },
        {
            "name": "Count all churches",
            "query": lambda: db.session.query(func.count(Church.id)).scalar()
        },
        {
            "name": "People with pagination (page 1)",
            "query": lambda: Person.query.paginate(page=1, per_page=100).items
        },
        {
            "name": "People with pagination (page 10)",
            "query": lambda: Person.query.paginate(page=10, per_page=100).items
        },
        {
            "name": "People with church associations",
            "query": lambda: Person.query.join(Person.churches).limit(100).all()
        },
        {
            "name": "Search people by name",
            "query": lambda: Person.query.filter(Person.first_name.ilike('%test%')).limit(100).all()
        },
        {
            "name": "Search churches by name",
            "query": lambda: Church.query.filter(Church.name.ilike('%test%')).limit(100).all()
        },
        {
            "name": "Pending tasks",
            "query": lambda: Task.query.filter_by(status='pending').limit(100).all()
        },
        {
            "name": "Recent communications",
            "query": lambda: Communication.query.order_by(Communication.date.desc()).limit(100).all()
        },
        {
            "name": "Aggregate query - people count by church",
            "query": lambda: db.session.query(
                Church.name, func.count(Person.id)
            ).join(Church.people).group_by(Church.name).limit(100).all()
        }
    ]
    
    results = []
    
    for query_info in queries:
        name = query_info["name"]
        query_func = query_info["query"]
        
        # Run the query multiple times to get an average
        times = []
        for _ in range(5):
            start_time = time.time()
            try:
                result = query_func()
                if hasattr(result, "__len__"):
                    result_count = len(result)
                else:
                    result_count = result
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            except Exception as e:
                logger.error(f"Error executing query '{name}': {str(e)}")
                break
        
        if times:
            avg_time = statistics.mean(times)
            results.append({
                "name": name,
                "avg_time_ms": avg_time,
                "result_count": result_count
            })
            logger.info(f"Query '{name}' - Avg time: {avg_time:.2f}ms - Results: {result_count}")
    
    # Sort results by average time (slowest first)
    results.sort(key=lambda x: x["avg_time_ms"], reverse=True)
    
    logger.info("\nQuery Performance Summary (sorted by execution time):")
    for result in results:
        logger.info(f"{result['name']}: {result['avg_time_ms']:.2f}ms - Results: {result['result_count']}")
    
    return results

def test_caching_effectiveness(app, db):
    """Test the effectiveness of caching"""
    from app.models.person import Person
    
    logger.info("Testing caching effectiveness...")
    
    # Test uncached query
    logger.info("Testing uncached query...")
    uncached_times = []
    for _ in range(5):
        start_time = time.time()
        people = Person.query.limit(100).all()
        end_time = time.time()
        uncached_times.append((end_time - start_time) * 1000)
    
    # Now with caching (assumes caching is implemented in the app)
    logger.info("Testing cached query...")
    from app.extensions import cache
    
    @cache.cached(timeout=60, key_prefix="test_cache")
    def get_cached_people():
        return Person.query.limit(100).all()
    
    cached_times = []
    for _ in range(5):
        start_time = time.time()
        people = get_cached_people()
        end_time = time.time()
        cached_times.append((end_time - start_time) * 1000)
    
    avg_uncached = statistics.mean(uncached_times)
    avg_cached = statistics.mean(cached_times)
    improvement = ((avg_uncached - avg_cached) / avg_uncached) * 100 if avg_uncached > 0 else 0
    
    logger.info(f"Uncached query average time: {avg_uncached:.2f}ms")
    logger.info(f"Cached query average time: {avg_cached:.2f}ms")
    logger.info(f"Caching improvement: {improvement:.2f}%")
    
    return {
        "uncached_avg_ms": avg_uncached,
        "cached_avg_ms": avg_cached,
        "improvement_percent": improvement
    }

def main():
    parser = argparse.ArgumentParser(description="Large Dataset Performance Test")
    parser.add_argument("--generate", action="store_true", help="Generate large test dataset")
    parser.add_argument("--people", type=int, default=1000, help="Number of people to generate")
    parser.add_argument("--churches", type=int, default=200, help="Number of churches to generate")
    parser.add_argument("--query-test", action="store_true", help="Run query performance tests")
    parser.add_argument("--cache-test", action="store_true", help="Test caching effectiveness")
    args = parser.parse_args()
    
    # Import app and db from the main application
    from app import create_app, db
    app = create_app()
    
    with app.app_context():
        if args.generate:
            generate_test_data(app, db, args.people, args.churches)
        
        if args.query_test:
            test_query_performance(app, db)
        
        if args.cache_test:
            test_caching_effectiveness(app, db)
        
        if not (args.generate or args.query_test or args.cache_test):
            logger.info("No actions specified. Use --generate, --query-test, or --cache-test")
            parser.print_help()

if __name__ == "__main__":
    main() 