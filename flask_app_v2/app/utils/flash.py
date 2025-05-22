"""
Flash message handling for both regular and AJAX requests
"""
from flask import flash as flask_flash, jsonify, request


def flash(message, category='info'):
    """
    Flash a message for both regular and AJAX requests
    
    Args:
        message (str): Message to flash
        category (str): Message category (info, success, warning, error)
        
    Returns:
        None for regular requests, JSON response for AJAX requests
    """
    # If this is an AJAX request, return JSON instead of flashing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        status_code = 200
        if category == 'error':
            status_code = 400
        
        return jsonify({
            'flash': {
                'message': message,
                'category': category
            }
        }), status_code
    
    # Otherwise, use regular Flask flash
    flask_flash(message, category)
    return None


def error_flash(message, status_code=400):
    """
    Flash an error message
    
    Args:
        message (str): Error message
        status_code (int): HTTP status code for AJAX requests
        
    Returns:
        None for regular requests, JSON response for AJAX requests
    """
    # If this is an AJAX request, return JSON instead of flashing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': False,
            'error': message,
            'flash': {
                'message': message,
                'category': 'error'
            }
        }), status_code
    
    # Otherwise, use regular Flask flash
    flask_flash(message, 'error')
    return None


def success_flash(message, data=None):
    """
    Flash a success message
    
    Args:
        message (str): Success message
        data (dict, optional): Additional data to include in AJAX response
        
    Returns:
        None for regular requests, JSON response for AJAX requests
    """
    # If this is an AJAX request, return JSON instead of flashing
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response = {
            'success': True,
            'message': message,
            'flash': {
                'message': message,
                'category': 'success'
            }
        }
        
        if data:
            response['data'] = data
            
        return jsonify(response)
    
    # Otherwise, use regular Flask flash
    flask_flash(message, 'success')
    return None
