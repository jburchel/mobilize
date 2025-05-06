"""Utility functions for handling system logs."""

import os
import re
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

def get_activity_logs(max_entries=100):
    """Get user activity logs."""
    try:
        # In a real implementation, this would query a database table
        # For now, we'll return an empty list as we'll implement this later
        return []
    except Exception as e:
        current_app.logger.error(f"Error getting activity logs: {str(e)}")
        return []

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
