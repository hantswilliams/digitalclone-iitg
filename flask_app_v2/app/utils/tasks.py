"""
Task status monitoring utilities
"""
from flask import jsonify, current_app
from celery.result import AsyncResult
from app.extensions import celery


def get_task_status(task_id):
    """
    Get the status of a Celery task
    
    Args:
        task_id (str): Celery task ID
        
    Returns:
        dict: Task status information
    """
    task = AsyncResult(task_id, app=celery)
    
    # Base response with task status
    response = {
        'task_id': task_id,
        'status': task.status
    }
    
    # Add result if task is complete
    if task.ready():
        if task.successful():
            # Successfully completed task
            response['result'] = task.result
            
            # Convert result to serializable format if needed
            if not isinstance(task.result, (dict, list, str, int, float, bool, type(None))):
                try:
                    response['result'] = str(task.result)
                except Exception as e:
                    current_app.logger.error(f"Error serializing task result: {str(e)}")
                    response['result'] = {'error': 'Could not serialize task result'}
        else:
            # Task failed
            response['status'] = 'FAILURE'
            
            # Extract exception information
            try:
                exception_info = {
                    'error': str(task.result),
                    'traceback': task.traceback
                }
                response['result'] = exception_info
            except Exception as e:
                current_app.logger.error(f"Error extracting exception info: {str(e)}")
                response['result'] = {'error': 'Task failed with an unknown error'}
    else:
        # Task still pending or running
        task_info = task.info
        
        # Get progress information if available
        if isinstance(task_info, dict):
            # Add metadata if provided by the task
            response['meta'] = task_info
    
    return response


def create_task_response(task_result, task_name=None):
    """
    Create a standardized API response for a task submission
    
    Args:
        task_result (celery.result.AsyncResult): Task result object
        task_name (str, optional): Name of the task
        
    Returns:
        tuple: JSON response and status code
    """
    if not task_result:
        return jsonify({
            'success': False,
            'error': 'Task could not be started',
        }), 500
        
    # Include task information in response
    response = {
        'success': True,
        'message': f"{task_name or 'Task'} started successfully",
        'data': {
            'task_id': task_result.id,
            'status': task_result.state,
            'status_url': f"/api/tasks/{task_result.id}"
        }
    }
    
    return jsonify(response), 202  # 202 Accepted
