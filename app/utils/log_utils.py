"""Utility functions for handling system logs."""

import os
import re
import random
import datetime
from flask import current_app
from collections import defaultdict

# Define log levels and their priorities
LOG_LEVELS = {
    'DEBUG': 0,
    'INFO': 1,
    'WARNING': 2,
    'ERROR': 3,
    'CRITICAL': 4
}

# Define log colors for different levels
LOG_COLORS = {
    'DEBUG': 'text-secondary',
    'INFO': 'text-info',
    'WARNING': 'text-warning',
    'ERROR': 'text-danger',
    'CRITICAL': 'text-danger fw-bold'
}

# Define regex patterns for parsing different log formats
LOG_PATTERNS = {
    'standard': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\] (\w+): (.+)'),
    'flask': re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)'),
    'gunicorn': re.compile(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} [+-]\d{4})\] \[(\w+)\] \[.+\] (.+)')
}

def get_log_files():
    """Get a list of all log files in the application log directory."""
    try:
        log_dir = get_log_directory()
        log_files = []
        
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    file_path = os.path.join(log_dir, filename)
                    file_size = os.path.getsize(file_path)
                    modified_time = os.path.getmtime(file_path)
                    
                    log_files.append({
                        'name': filename,
                        'path': file_path,
                        'size': format_file_size(file_size),
                        'size_bytes': file_size,
                        'modified': datetime.datetime.fromtimestamp(modified_time)
                    })
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        return log_files
    except Exception as e:
        current_app.logger.error(f"Error getting log files: {str(e)}")
        return []

def get_log_directory():
    """Get the log directory path."""
    try:
        # Try to get log directory from app config
        if current_app.config.get('LOG_DIR'):
            return current_app.config.get('LOG_DIR')
        
        # Default to instance/logs directory
        log_dir = os.path.join(current_app.instance_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except Exception as e:
        current_app.logger.error(f"Error getting log directory: {str(e)}")
        # Fallback to a relative logs directory
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')

def format_file_size(size_bytes):
    """Format file size in bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

def parse_log_file(file_path, max_entries=1000, level_filter=None, search_term=None):
    """Parse a log file and return structured log entries."""
    try:
        if not os.path.exists(file_path):
            return []
        
        log_entries = []
        line_count = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_count += 1
                if line_count > max_entries:
                    break
                
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Try to parse the line using different patterns
                entry = None
                for pattern_name, pattern in LOG_PATTERNS.items():
                    match = pattern.match(line.strip())
                    if match:
                        timestamp_str, level, message = match.groups()
                        
                        # Apply level filter if specified
                        if level_filter and level != level_filter:
                            continue
                        
                        # Apply search filter if specified
                        if search_term and search_term.lower() not in message.lower():
                            continue
                        
                        # Parse timestamp
                        try:
                            if pattern_name == 'gunicorn':
                                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S %z')
                            else:
                                timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        except ValueError:
                            timestamp = datetime.datetime.now()  # Fallback if parsing fails
                        
                        entry = {
                            'timestamp': timestamp,
                            'level': level,
                            'message': message,
                            'color': LOG_COLORS.get(level, 'text-secondary')
                        }
                        break
                
                # If no pattern matched, treat as continuation of previous message
                if not entry and log_entries:
                    log_entries[-1]['message'] += '\n' + line.strip()
                elif entry:
                    log_entries.append(entry)
        
        # Sort by timestamp (newest first)
        log_entries.sort(key=lambda x: x['timestamp'], reverse=True)
        return log_entries
    except Exception as e:
        current_app.logger.error(f"Error parsing log file {file_path}: {str(e)}")
        return []

def get_system_logs(max_entries=1000, level_filter=None, search_term=None):
    """Get system logs from the application log files."""
    try:
        log_files = get_log_files()
        if not log_files:
            return []
        
        # Use the most recent log file by default
        most_recent_log = log_files[0]['path']
        return parse_log_file(most_recent_log, max_entries, level_filter, search_term)
    except Exception as e:
        current_app.logger.error(f"Error getting system logs: {str(e)}")
        return []

def get_log_statistics(logs=None):
    """Get statistics about the logs."""
    if logs is None:
        logs = get_system_logs(max_entries=10000)  # Get a larger sample for statistics
    
    stats = {
        'total_entries': len(logs),
        'level_counts': defaultdict(int),
        'hourly_distribution': defaultdict(int),
        'daily_distribution': defaultdict(int),
        'recent_errors': []
    }
    
    # Current time for calculating recency
    now = datetime.datetime.now()
    
    for entry in logs:
        # Count by level
        level = entry.get('level', 'UNKNOWN')
        stats['level_counts'][level] += 1
        
        # Hourly distribution
        timestamp = entry.get('timestamp')
        if timestamp:
            hour = timestamp.hour
            day_of_week = timestamp.strftime('%A')
            
            stats['hourly_distribution'][hour] += 1
            stats['daily_distribution'][day_of_week] += 1
            
            # Collect recent errors (last 24 hours)
            if level in ['ERROR', 'CRITICAL'] and (now - timestamp).total_seconds() < 86400:  # 24 hours in seconds
                stats['recent_errors'].append(entry)
    
    # Sort recent errors by timestamp (newest first)
    stats['recent_errors'].sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to top 10 recent errors
    stats['recent_errors'] = stats['recent_errors'][:10]
    
    return stats

def get_activity_logs(max_entries=100, level_filter=None, search_term=None, days=30):
    """Get user activity logs from the activity log file.
    
    Args:
        max_entries (int): Maximum number of log entries to return
        level_filter (str): Filter logs by level (e.g., 'SUCCESS', 'FAILURE')
        search_term (str): Filter logs by search term
        days (int): Number of days to look back for logs
        
    Returns:
        list: List of activity log entries
    """
    try:
        log_dir = get_log_directory()
        activity_log_path = os.path.join(log_dir, 'activity.log')
        
        # If the activity log file doesn't exist, create it with some initial entries
        if not os.path.exists(activity_log_path):
            create_sample_activity_logs(activity_log_path)
        
        # Read the activity log file
        activities = []
        with open(activity_log_path, 'r') as f:
            for line in f:
                try:
                    # Parse the log entry
                    # Format: [timestamp] [status] [subsystem] [operation] [user] [ip] [description]
                    parts = line.strip().split('|')
                    if len(parts) >= 7:
                        timestamp_str = parts[0].strip()
                        status = parts[1].strip()
                        subsystem = parts[2].strip()
                        operation = parts[3].strip()
                        user_info = parts[4].strip()
                        ip_address = parts[5].strip()
                        description = parts[6].strip()
                        
                        # Parse additional fields if available
                        impact = parts[7].strip() if len(parts) > 7 else 'MEDIUM'
                        resource_id = parts[8].strip() if len(parts) > 8 else None
                        duration = int(parts[9]) if len(parts) > 9 and parts[9].strip().isdigit() else None
                        
                        # Parse timestamp
                        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        # Parse user info (format: name <email>)
                        email = None
                        if '<' in user_info and '>' in user_info:
                            user_name, email = user_info.split('<', 1)
                            user_name = user_name.strip()
                            email = email.split('>', 1)[0].strip()
                        else:
                            user_name = user_info
                        
                        # Apply filters
                        # Filter by days
                        if (datetime.datetime.now() - timestamp).days > days:
                            continue
                            
                        # Filter by level
                        if level_filter and status != level_filter:
                            continue
                            
                        # Filter by search term
                        if search_term and search_term.lower() not in (
                            description.lower() + 
                            subsystem.lower() + 
                            operation.lower() + 
                            user_name.lower() + 
                            (email.lower() if email else '')
                        ):
                            continue
                        
                        # Add the activity to the list
                        activities.append({
                            'timestamp': timestamp,
                            'subsystem': subsystem,
                            'operation': operation,
                            'description': description,
                            'status': status,
                            'impact': impact,
                            'user': user_name,
                            'email': email,
                            'ip_address': ip_address if ip_address != 'None' else None,
                            'duration': duration,
                            'resource_id': resource_id if resource_id != 'None' else None
                        })
                except Exception as e:
                    current_app.logger.error(f"Error parsing activity log line: {str(e)}")
                    continue
        
        # Sort activities by timestamp in descending order
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limit the number of entries
        activities = activities[:max_entries]
        
        return activities
    except Exception as e:
        current_app.logger.error(f"Error getting activity logs: {str(e)}")
        return []

def create_sample_activity_logs(log_path):
    """Create sample activity logs for demonstration purposes."""
    try:
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        # Sample data
        now = datetime.datetime.now()
        subsystems = ['Authentication', 'Database', 'API', 'File System', 'Background Jobs', 
                    'Email Service', 'Payment Processing', 'User Management', 'Church Management']
        operations = ['CREATE', 'READ', 'UPDATE', 'DELETE', 'IMPORT', 'EXPORT', 'SCHEDULE', 
                    'CANCEL', 'PROCESS', 'SYNC', 'BACKUP', 'RESTORE']
        statuses = ['SUCCESS', 'FAILURE', 'WARNING', 'PENDING', 'TIMEOUT', 'ABORTED']
        impacts = ['HIGH', 'MEDIUM', 'LOW', 'NONE']
        users = [
            'System Admin <admin@example.com>',
            'John Doe <john.doe@example.com>',
            'Jane Smith <jane.smith@example.com>',
            'Pastor Williams <pastor@church.org>',
            'Sarah Johnson <coordinator@ministry.com>',
            'System'  # For system activities with no user
        ]
        
        # Generate sample logs
        with open(log_path, 'w') as f:
            for i in range(100):
                # Random timestamp in the last 30 days
                days_ago = random.randint(0, 30)
                hours_ago = random.randint(0, 23)
                mins_ago = random.randint(0, 59)
                timestamp = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
                timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Random values
                subsystem = random.choice(subsystems)
                operation = random.choice(operations)
                status_weights = [0.7, 0.1, 0.1, 0.05, 0.025, 0.025]  # Probabilities for each status
                status = random.choices(statuses, weights=status_weights, k=1)[0]
                
                # Random impact level based on status
                if status == 'SUCCESS':
                    impact = random.choices(impacts, weights=[0.05, 0.15, 0.3, 0.5], k=1)[0]
                elif status == 'FAILURE':
                    impact = random.choices(impacts, weights=[0.6, 0.3, 0.1, 0], k=1)[0]
                else:
                    impact = random.choices(impacts, weights=[0.2, 0.4, 0.3, 0.1], k=1)[0]
                
                # Random user
                user = random.choice(users)
                
                # Generate IP address (None for system user)
                ip_address = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}" if user != 'System' else 'None'
                
                # Generate description
                if subsystem == 'Authentication':
                    resource = random.choice(['user session', 'password', 'account', 'token'])
                    if operation == 'CREATE':
                        description = f"New {resource} created"
                    elif operation in ['UPDATE', 'PROCESS']:
                        description = f"{resource.capitalize()} updated"
                    elif operation == 'DELETE':
                        description = f"{resource.capitalize()} removed"
                    else:
                        description = f"{operation.capitalize()} operation on {resource}"
                elif subsystem == 'Database':
                    resource = random.choice(['record', 'table', 'query', 'connection', 'index'])
                    description = f"Database {operation.lower()} on {resource}"
                elif subsystem == 'API':
                    resource = random.choice(['endpoint', 'request', 'response', 'integration'])
                    description = f"API {operation.lower()} - {resource}"
                elif subsystem in ['User Management', 'Church Management']:
                    resource = random.choice(['profile', 'role', 'permission', 'group', 'membership'])
                    description = f"{subsystem} {operation.lower()} - {resource}"
                else:
                    description = f"{subsystem} {operation.lower()} operation"
                
                # Add more details for failed operations
                if status == 'FAILURE':
                    description += " - " + random.choice([
                        "Resource not found", 
                        "Permission denied",
                        "Validation error",
                        "Timeout exceeded",
                        "Conflict detected",
                        "Rate limit reached",
                        "Invalid input"
                    ])
                
                # Random resource ID and duration
                resource_id = f"{random.randint(1000, 9999)}" if random.random() > 0.3 else 'None'
                duration = str(random.randint(1, 5000)) if operation not in ['CREATE', 'DELETE'] else 'None'
                
                # Write the log entry
                log_entry = f"{timestamp_str}|{status}|{subsystem}|{operation}|{user}|{ip_address}|{description}|{impact}|{resource_id}|{duration}"
                f.write(log_entry + '\n')
    except Exception as e:
        current_app.logger.error(f"Error creating sample activity logs: {str(e)}")

def log_activity(subsystem, operation, description, status='SUCCESS', impact='MEDIUM', user=None, ip_address=None, resource_id=None, duration=None):
    """Log a user activity to the activity log file.
    
    Args:
        subsystem (str): The subsystem where the activity occurred (e.g., 'Authentication', 'Database')
        operation (str): The operation performed (e.g., 'CREATE', 'UPDATE', 'DELETE')
        description (str): A description of the activity
        status (str): The status of the activity (e.g., 'SUCCESS', 'FAILURE')
        impact (str): The impact level of the activity (e.g., 'HIGH', 'MEDIUM', 'LOW')
        user (dict): User information (should have 'name' and 'email' keys)
        ip_address (str): The IP address of the user
        resource_id (str): The ID of the resource being operated on
        duration (int): The duration of the operation in milliseconds
    """
    try:
        log_dir = get_log_directory()
        activity_log_path = os.path.join(log_dir, 'activity.log')
        
        # Create the log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Format the timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the user information
        if user and 'name' in user and 'email' in user:
            user_info = f"{user['name']} <{user['email']}>"
        elif user and 'name' in user:
            user_info = user['name']
        else:
            user_info = 'System'
        
        # Format the log entry
        log_entry = f"{timestamp}|{status}|{subsystem}|{operation}|{user_info}|{ip_address or 'None'}|{description}|{impact}|{resource_id or 'None'}|{duration or 'None'}"
        
        # Write to the log file
        with open(activity_log_path, 'a') as f:
            f.write(log_entry + '\n')
    except Exception as e:
        current_app.logger.error(f"Error logging activity: {str(e)}")


def get_security_logs(max_entries=100):
    """Get security logs."""
    try:
        # In a real implementation, this would query a database table
        # For now, we'll return an empty list as we'll implement this later
        return []
    except Exception as e:
        current_app.logger.error(f"Error getting security logs: {str(e)}")
        return []

def log_system_event(level, message):
    """Log a system event."""
    try:
        if level == 'DEBUG':
            current_app.logger.debug(message)
        elif level == 'INFO':
            current_app.logger.info(message)
        elif level == 'WARNING':
            current_app.logger.warning(message)
        elif level == 'ERROR':
            current_app.logger.error(message)
        elif level == 'CRITICAL':
            current_app.logger.critical(message)
    except Exception:
        # If we can't log through the app logger, try to write directly to a file
        try:
            log_dir = get_log_directory()
            log_file = os.path.join(log_dir, 'system.log')
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
            with open(log_file, 'a') as f:
                f.write(f"[{timestamp}] {level}: {message}\n")
        except Exception:
            pass  # Last resort - if we can't log, we can't log the error either
