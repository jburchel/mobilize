"""
Health check endpoints for monitoring application status.
"""

from flask import Blueprint, jsonify, current_app
import datetime
import os
import platform
import psutil
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def basic_health_check():
    """Basic health check endpoint."""
    return jsonify({
        'status': 'ok',
        'time': datetime.datetime.now().isoformat(),
        'message': 'Basic health check passed'
    }), 200

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with system information."""
    # Check database connection
    db_status = 'ok'
    db_message = 'Connected'
    try:
        from app.extensions import db
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
    except Exception as e:
        db_status = 'error'
        db_message = str(e)
    
    # Get system metrics
    system_metrics = {
        'cpu_percent': psutil.cpu_percent(interval=0.1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'boot_time': datetime.datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        'process_create_time': datetime.datetime.fromtimestamp(psutil.Process().create_time()).isoformat()
    }
    
    # Get application metrics
    app_metrics = {
        'uptime_seconds': time.time() - psutil.Process().create_time(),
        'environment': os.environ.get('FLASK_ENV', 'unknown'),
        'python_version': platform.python_version(),
        'platform': platform.platform()
    }
    
    return jsonify({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'time': datetime.datetime.now().isoformat(),
        'components': {
            'database': {
                'status': db_status,
                'message': db_message
            }
        },
        'system': system_metrics,
        'application': app_metrics
    }), 200

@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/Cloud Run."""
    # Check if the application is ready to receive traffic
    all_ready = True
    components = {}
    
    # Check database
    try:
        from app.extensions import db
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        components['database'] = {'status': 'ready'}
    except Exception as e:
        all_ready = False
        components['database'] = {
            'status': 'not_ready',
            'message': str(e)
        }
    
    # Check cache if configured
    if hasattr(current_app, 'cache'):
        try:
            current_app.cache.set('health_check', 'ok')
            test_value = current_app.cache.get('health_check')
            if test_value == 'ok':
                components['cache'] = {'status': 'ready'}
            else:
                all_ready = False
                components['cache'] = {'status': 'not_ready', 'message': 'Cache test failed'}
        except Exception as e:
            all_ready = False
            components['cache'] = {
                'status': 'not_ready',
                'message': str(e)
            }
    
    status_code = 200 if all_ready else 503
    return jsonify({
        'status': 'ready' if all_ready else 'not_ready',
        'time': datetime.datetime.now().isoformat(),
        'components': components
    }), status_code