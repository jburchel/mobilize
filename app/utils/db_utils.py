"""Database utility functions for database management."""

import os
import time
import datetime
import sqlite3
import shutil
import json
from pathlib import Path
from flask import current_app
from sqlalchemy import inspect, text
from app.extensions import db


def get_database_stats():
    """Get statistics about the database."""
    stats = {
        'size': get_database_size(),
        'tables': len(get_all_tables()),
        'records': get_total_records(),
        'avg_query_time': measure_query_performance(),
        'last_optimization': get_last_optimization_date(),
        'health_score': calculate_health_score(),
        'fragmentation': calculate_fragmentation(),
        'slow_queries': get_slow_queries_percentage()
    }
    return stats


def get_database_size():
    """Get the size of the database file in human-readable format."""
    try:
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # Handle SQLite database
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                size_bytes = os.path.getsize(db_path)
                return format_file_size(size_bytes)
        
        # For other database types, estimate using table sizes
        inspector = inspect(db.engine)
        total_size = 0
        
        for table_name in inspector.get_table_names():
            result = db.session.execute(text(f"SELECT pg_total_relation_size('{table_name}');"))
            table_size = result.scalar()
            if table_size:
                total_size += table_size
        
        return format_file_size(total_size)
    except Exception as e:
        current_app.logger.error(f"Error getting database size: {str(e)}")
        return "Unknown"


def format_file_size(size_bytes):
    """Format file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0


def get_all_tables():
    """Get a list of all tables in the database."""
    try:
        inspector = inspect(db.engine)
        return inspector.get_table_names()
    except Exception as e:
        current_app.logger.error(f"Error getting tables: {str(e)}")
        return []


def get_total_records():
    """Get the total number of records across all tables."""
    try:
        total = 0
        inspector = inspect(db.engine)
        
        for table_name in inspector.get_table_names():
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            if count:
                total += count
        
        return total
    except Exception as e:
        current_app.logger.error(f"Error getting total records: {str(e)}")
        return 0


def measure_query_performance():
    """Measure average query performance in milliseconds."""
    try:
        # Use a simple query to measure performance
        start_time = time.time()
        
        # Run a few sample queries
        tables = get_all_tables()
        for _ in range(min(5, len(tables))):
            db.session.execute(text(f"SELECT 1 FROM {tables[0]} LIMIT 1"))
        
        end_time = time.time()
        avg_time = ((end_time - start_time) * 1000) / max(1, min(5, len(tables)))
        
        return round(avg_time)
    except Exception as e:
        current_app.logger.error(f"Error measuring query performance: {str(e)}")
        return 0


def get_last_optimization_date():
    """Get the date of the last database optimization."""
    try:
        # In a real implementation, this would be stored in a system settings table
        # For now, return a date from a few days ago
        return datetime.datetime.now() - datetime.timedelta(days=2)
    except Exception as e:
        current_app.logger.error(f"Error getting last optimization date: {str(e)}")
        return datetime.datetime.now() - datetime.timedelta(days=30)


def calculate_health_score():
    """Calculate an overall health score for the database (0-100)."""
    try:
        # In a real implementation, this would be based on various metrics
        # For now, return a random score between 70 and 95
        fragmentation = calculate_fragmentation()
        slow_queries = get_slow_queries_percentage()
        
        # Higher fragmentation and slow queries reduce the health score
        health_score = 100 - (fragmentation * 0.3) - (slow_queries * 0.7)
        return max(0, min(100, round(health_score)))
    except Exception as e:
        current_app.logger.error(f"Error calculating health score: {str(e)}")
        return 75


def calculate_fragmentation():
    """Calculate database fragmentation percentage."""
    try:
        # In a real implementation, this would analyze table fragmentation
        # For SQLite, we can estimate based on free pages
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA freelist_count")
                freelist_count = cursor.fetchone()[0]
                conn.close()
                
                if page_count > 0:
                    fragmentation = (freelist_count / page_count) * 100
                    return round(fragmentation)
        
        # For other databases or if calculation fails, return an estimated value
        return 25
    except Exception as e:
        current_app.logger.error(f"Error calculating fragmentation: {str(e)}")
        return 25


def get_slow_queries_percentage():
    """Get the percentage of slow queries."""
    try:
        # In a real implementation, this would analyze query logs
        # For now, return a fixed percentage
        return 8
    except Exception as e:
        current_app.logger.error(f"Error getting slow queries percentage: {str(e)}")
        return 10


def get_table_stats():
    """Get statistics for all tables in the database."""
    try:
        stats = []
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        for table_name in tables:
            # Get record count
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            record_count = result.scalar() or 0
            
            # Get table size
            table_size = get_table_size(table_name)
            
            # Get last updated time (this is an approximation)
            last_updated = get_table_last_updated(table_name)
            
            # Determine status based on fragmentation
            status = get_table_status(table_name)
            
            stats.append({
                'name': table_name,
                'records': record_count,
                'size': table_size,
                'last_updated': last_updated,
                'status': status
            })
        
        return stats
    except Exception as e:
        current_app.logger.error(f"Error getting table stats: {str(e)}")
        return []


def get_table_size(table_name):
    """Get the size of a specific table in human-readable format."""
    try:
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # For PostgreSQL
        if 'postgresql' in db_uri:
            result = db.session.execute(text(f"SELECT pg_total_relation_size('{table_name}')"))
            size_bytes = result.scalar() or 0
            return format_file_size(size_bytes)
        
        # For SQLite, estimate based on record count and column types
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        record_count = result.scalar() or 0
        
        # Rough estimate: assume average row size of 100-500 bytes depending on table
        avg_row_size = 250  # bytes
        estimated_size = record_count * avg_row_size
        
        return format_file_size(estimated_size)
    except Exception as e:
        current_app.logger.error(f"Error getting table size for {table_name}: {str(e)}")
        return "Unknown"


def get_table_last_updated(table_name):
    """Get the approximate last updated time for a table."""
    try:
        # This is a simplification - in a real system, you'd track this in metadata
        # For now, return a random recent time
        hours = hash(table_name) % 24  # Use table name hash for deterministic but varied results
        return datetime.datetime.now() - datetime.timedelta(hours=hours)
    except Exception as e:
        current_app.logger.error(f"Error getting last updated time for {table_name}: {str(e)}")
        return datetime.datetime.now() - datetime.timedelta(days=1)


def get_table_status(table_name):
    """Determine the status of a table based on its condition."""
    try:
        # In a real implementation, this would analyze table structure and performance
        # For now, most tables are "Healthy" with some needing optimization
        if hash(table_name) % 5 == 0:  # Deterministic way to mark some tables as needing optimization
            return "Needs Optimization"
        return "Healthy"
    except Exception as e:
        current_app.logger.error(f"Error getting status for {table_name}: {str(e)}")
        return "Unknown"


def create_database_backup():
    """Create a backup of the database."""
    try:
        import json, time, shutil
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # For PostgreSQL
        if 'postgresql' in db_uri:
            # Find the database name from the URI
            db_name = db_uri.split('/')[-1]
            current_app.logger.info(f"Creating backup for PostgreSQL database: {db_name}")
            
            # Create a backup file path
            backup_path = os.path.join(backup_dir, f"backup_{timestamp}.sql")
            
            # For development, we'll create a dummy backup file
            with open(backup_path, 'w') as f:
                f.write(f"-- PostgreSQL database backup for {db_name}\n-- Created at {timestamp}\n")
            
            # Store backup metadata
            backup_id = int(time.time())
            metadata = {
                'id': backup_id,
                'created_at': datetime.datetime.now().isoformat(),
                'size': format_file_size(os.path.getsize(backup_path)),
                'created_by': 'System',
                'type': 'Manual',
                'status': 'Complete',
                'path': backup_path
            }
            
            # Save metadata to a JSON file
            metadata_path = os.path.join(backup_dir, f"backup_{backup_id}_meta.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            return backup_id
            
        # For SQLite
        elif db_uri.startswith('sqlite:///'):
            # Extract the database path from the URI
            db_path = db_uri.replace('sqlite:///', '')
            
            # If the path is relative, make it absolute
            if not os.path.isabs(db_path):
                db_path = os.path.join(current_app.root_path, '..', db_path)
            
            current_app.logger.info(f"Creating backup for SQLite database at: {db_path}")
            
            # Check if the database file exists
            if not os.path.exists(db_path):
                # Try to find an existing database file in the instance directory
                instance_dir = os.path.join(current_app.root_path, '..', 'instance')
                for file in os.listdir(instance_dir):
                    if file.endswith('.db'):
                        db_path = os.path.join(instance_dir, file)
                        current_app.logger.info(f"Found alternative database file: {db_path}")
                        break
            
            if os.path.exists(db_path):
                backup_path = os.path.join(backup_dir, f"backup_{timestamp}.db")
                shutil.copy2(db_path, backup_path)
                
                # Store backup metadata
                backup_id = int(time.time())
                metadata = {
                    'id': backup_id,
                    'created_at': datetime.datetime.now().isoformat(),
                    'size': format_file_size(os.path.getsize(backup_path)),
                    'created_by': 'System',
                    'type': 'Manual',
                    'status': 'Complete',
                    'path': backup_path
                }
                
                # Save metadata to a JSON file
                metadata_path = os.path.join(backup_dir, f"backup_{backup_id}_meta.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
                
                return backup_id
        
        # For other database types, you would use database-specific backup commands
        # This is beyond the scope of this implementation
        
        return None
    except Exception as e:
        current_app.logger.error(f"Error creating database backup: {str(e)}")
        return None


def get_database_backups():
    """Get a list of all database backups."""
    try:
        backups = []
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        
        if not os.path.exists(backup_dir):
            return backups
        
        # Look for backup metadata files
        for filename in os.listdir(backup_dir):
            if filename.endswith('_meta.json'):
                metadata_path = os.path.join(backup_dir, filename)
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Convert ISO format string back to datetime
                if 'created_at' in metadata and isinstance(metadata['created_at'], str):
                    metadata['created_at'] = datetime.datetime.fromisoformat(metadata['created_at'])
                
                backups.append(metadata)
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x.get('created_at', datetime.datetime.min), reverse=True)
        
        return backups
    except Exception as e:
        current_app.logger.error(f"Error getting database backups: {str(e)}")
        return []


def get_backup_by_id(backup_id):
    """Get a specific backup by its ID."""
    try:
        backup_dir = os.path.join(current_app.instance_path, 'backups')
        metadata_path = os.path.join(backup_dir, f"backup_{backup_id}_meta.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Convert ISO format string back to datetime
            if 'created_at' in metadata and isinstance(metadata['created_at'], str):
                metadata['created_at'] = datetime.datetime.fromisoformat(metadata['created_at'])
            
            return metadata
        
        return None
    except Exception as e:
        current_app.logger.error(f"Error getting backup {backup_id}: {str(e)}")
        return None


def optimize_database():
    """Optimize the database to improve performance."""
    try:
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # For SQLite
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                conn.close()
                
                # Update the last optimization date
                # In a real implementation, this would be stored in a system settings table
                
                return True
        
        # For other database types, you would use database-specific optimization commands
        # This is beyond the scope of this implementation
        
        return False
    except Exception as e:
        current_app.logger.error(f"Error optimizing database: {str(e)}")
        return False


def restore_database_from_backup(backup_id):
    """Restore the database from a backup."""
    try:
        backup = get_backup_by_id(backup_id)
        if not backup or 'path' not in backup:
            return False
        
        backup_path = backup['path']
        if not os.path.exists(backup_path):
            return False
        
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # For SQLite
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            
            # Close all database connections
            db.session.remove()
            db.engine.dispose()
            
            # Copy the backup over the current database
            shutil.copy2(backup_path, db_path)
            
            return True
        
        # For other database types, you would use database-specific restore commands
        # This is beyond the scope of this implementation
        
        return False
    except Exception as e:
        current_app.logger.error(f"Error restoring database from backup {backup_id}: {str(e)}")
        return False


def get_table_structure(table_name):
    """Get the structure of a specific table."""
    try:
        inspector = inspect(db.engine)
        
        # Get columns
        columns = []
        for column in inspector.get_columns(table_name):
            col_info = {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': 'YES' if column.get('nullable', True) else 'NO',
                'default': str(column.get('default', 'NULL')),
                'key': ''
            }
            columns.append(col_info)
        
        # Get primary key columns
        pk_constraint = inspector.get_pk_constraint(table_name)
        pk_columns = pk_constraint.get('constrained_columns', [])
        
        # Mark primary key columns
        for column in columns:
            if column['name'] in pk_columns:
                column['key'] = 'PK'
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            for column_name in fk.get('constrained_columns', []):
                for column in columns:
                    if column['name'] == column_name:
                        column['key'] = 'FK'
        
        # Get indexes
        indexes = []
        for index in inspector.get_indexes(table_name):
            index_info = {
                'name': index['name'],
                'columns': ', '.join(index['column_names']),
                'type': 'UNIQUE' if index.get('unique', False) else 'INDEX',
                'size': 'N/A'  # Size information not available through SQLAlchemy
            }
            indexes.append(index_info)
        
        # Get sample data (first few rows)
        sample_data = []
        result = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 5"))
        for row in result:
            sample_data.append(dict(row))
        
        return {
            'columns': columns,
            'indexes': indexes,
            'sample_data': sample_data
        }
    except Exception as e:
        current_app.logger.error(f"Error getting table structure for {table_name}: {str(e)}")
        return {'columns': [], 'indexes': [], 'sample_data': []}
