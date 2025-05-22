"""
API utility functions and decorators
"""
from flask import jsonify, request, current_app, session
from functools import wraps
from app.errors import APIError
import traceback


def api_response(success=True, message=None, data=None, error=None, status_code=200):
    """
    Create a standardized API response
    
    Args:
        success (bool): Whether the request was successful
        message (str, optional): A message describing the response
        data (dict, optional): The response data
        error (str, optional): Error message if unsuccessful
        status_code (int): HTTP status code
        
    Returns:
        tuple: JSON response and status code
    """
    response = {
        'success': success
    }
    
    if message:
        response['message'] = message
        
    if data is not None:
        response['data'] = data
        
    if error:
        response['error'] = error
        
    return jsonify(response), status_code


def api_error(message, status_code=400, details=None):
    """
    Create a standardized API error response
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code
        details (dict, optional): Additional error details
        
    Returns:
        tuple: JSON response and status code
    """
    response = {
        'success': False,
        'error': message
    }
    
    if details:
        response['details'] = details
        
    return jsonify(response), status_code


def handle_validation_error(error):
    """
    Handle form validation errors
    
    Args:
        error: Form validation error
        
    Returns:
        tuple: JSON response and status code
    """
    # Extract validation errors
    errors = {}
    for field, messages in error.errors.items():
        errors[field] = messages[0]  # Get first error message for each field
    
    return api_error(
        message="Validation error",
        status_code=400,
        details={"errors": errors}
    )


def login_required(f):
    """
    Decorator for routes that require authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_error("Authentication required", 401)
            return current_app.login_manager.unauthorized()
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator for routes that require admin privileges
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_error("Authentication required", 401)
            return current_app.login_manager.unauthorized()
        
        user = session['user']
        from app.models import User
        
        user_record = User.query.filter_by(user_id=user.get('sub')).first()
        if not user_record or user_record.permissions != 'admin':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return api_error("Admin privileges required", 403)
            return current_app.login_manager.unauthorized()
        
        return f(*args, **kwargs)
    return decorated_function


def handle_api_exception(f):
    """
    Decorator to handle exceptions in API routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError as e:
            current_app.logger.warning(f"API Error: {e.message}")
            return api_error(e.message, e.status_code, e.payload)
        except Exception as e:
            current_app.logger.error(f"Unhandled API Error: {str(e)}")
            current_app.logger.error(traceback.format_exc())
            
            if current_app.debug:
                error_details = {
                    'exception': str(e),
                    'traceback': traceback.format_exc().split('\n')
                }
                return api_error(
                    message=f"An unexpected error occurred: {str(e)}",
                    status_code=500,
                    details=error_details
                )
            
            return api_error(
                message="An unexpected error occurred",
                status_code=500
            )
    
    return decorated_function
