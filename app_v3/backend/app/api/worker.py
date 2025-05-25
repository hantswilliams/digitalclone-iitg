"""
Worker management API endpoints
"""
from flask import Blueprint, jsonify, current_app, request
from flask_jwt_extended import jwt_required
from ..extensions import redis_client

worker_bp = Blueprint('worker', __name__)


@worker_bp.route('/ping', methods=['GET'])
def ping_worker():
    """
    Health check endpoint for Celery workers
    Tests Redis connectivity and worker availability
    """
    try:
        # Test Redis connection
        if redis_client:
            try:
                redis_info = redis_client.ping()
                redis_status = "connected" if redis_info else "disconnected"
            except Exception as e:
                redis_status = f"connection_error: {str(e)}"
        else:
            redis_status = "not configured"
        
        # Test basic Celery connection without inspecting workers for now
        try:
            from ..extensions import celery
            broker_url = celery.conf.broker_url
            celery_status = f"configured with broker: {broker_url}"
        except Exception as e:
            celery_status = f"error: {str(e)}"
        
        return jsonify({
            'status': 'healthy',
            'redis_status': redis_status,
            'celery_status': celery_status,
            'message': 'Basic connectivity test'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'redis_status': 'error',
            'worker_status': 'error'
        }), 500


@worker_bp.route('/status', methods=['GET'])
def worker_status():
    """
    Get detailed worker status information
    """
    try:
        from ..extensions import celery
        inspect = celery.control.inspect()
        
        # Get various worker information
        active_tasks = inspect.active()
        scheduled_tasks = inspect.scheduled()
        reserved_tasks = inspect.reserved()
        stats = inspect.stats()
        
        return jsonify({
            'active_tasks': active_tasks,
            'scheduled_tasks': scheduled_tasks,
            'reserved_tasks': reserved_tasks,
            'worker_stats': stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@worker_bp.route('/test-echo', methods=['POST'])
@jwt_required()
def test_echo():
    """
    Test endpoint to trigger echo task
    """
    try:
        from ..tasks.voice_tasks import echo_task
        
        data = request.get_json() or {}
        message = data.get('message', 'Hello from test endpoint!')
        
        # Start echo task
        task_result = echo_task.delay(message)
        
        return jsonify({
            'message': 'Echo task started',
            'task_id': task_result.id,
            'test_message': message
        }), 202
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@worker_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status of a specific task
    """
    try:
        from ..extensions import celery
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id, app=celery)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': 'Task is waiting to be processed'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'progress': task_result.info.get('progress', 0),
                'status': task_result.info.get('status', '')
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'result': task_result.result
            }
        else:
            # Task failed
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'error': str(task_result.info)
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
