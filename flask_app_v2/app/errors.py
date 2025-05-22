"""
Error handling for the application
"""
from flask import Blueprint, render_template, jsonify, request

errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'code': 404
        }), 404
    return render_template('errors/404.html', title='Not Found'), 404


@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Forbidden. You do not have permission to access this resource',
            'code': 403
        }), 403
    return render_template('errors/403.html', title='Forbidden'), 403


@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'code': 500
        }), 500
    return render_template('errors/500.html', title='Server Error'), 500


@errors_bp.app_errorhandler(400)
def bad_request_error(error):
    """Handle 400 errors"""
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Bad request. Please check your input',
            'code': 400
        }), 400
    return render_template('errors/400.html', title='Bad Request'), 400


@errors_bp.app_errorhandler(401)
def unauthorized_error(error):
    """Handle 401 errors"""
    if request.path.startswith('/api'):
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'code': 401
        }), 401
    return render_template('errors/401.html', title='Unauthorized'), 401


class APIError(Exception):
    """Base exception for API errors"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convert exception to dictionary for JSON response"""
        result = {
            'success': False,
            'error': self.message,
            'code': self.status_code
        }
        if self.payload:
            result['details'] = self.payload
        return result


@errors_bp.app_errorhandler(APIError)
def handle_api_error(error):
    """Handle custom API errors"""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
