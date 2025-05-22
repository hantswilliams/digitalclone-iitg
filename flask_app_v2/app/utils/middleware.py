"""
Middleware for request tracking and error monitoring
"""
from flask import request, g, current_app
from time import time
import traceback
from functools import wraps


def init_request_middleware(app):
    """
    Initialize request tracking middleware
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request():
        """
        Actions to perform before each request
        """
        # Store start time to calculate request duration
        g.start_time = time()
        
        # Mark request as being processed
        g.request_handled = False
        
        # Generate a unique request ID
        import uuid
        g.request_id = str(uuid.uuid4())
        
        # Log incoming request in debug mode
        if app.debug:
            current_app.logger.debug(
                f"Incoming {request.method} request to {request.path} "
                f"from {request.remote_addr} [ID: {g.request_id}]"
            )
    
    @app.after_request
    def after_request(response):
        """
        Actions to perform after each request
        
        Args:
            response: Flask response object
        """
        # Calculate request duration
        if hasattr(g, 'start_time'):
            duration_ms = (time() - g.start_time) * 1000
            
            # Add timing header
            response.headers['X-Request-Time-Ms'] = str(int(duration_ms))
            
            # Log request completion
            current_app.logger.info(
                f"Request {request.method} {request.path} completed in {duration_ms:.2f}ms "
                f"with status {response.status_code} [ID: {g.get('request_id', 'unknown')}]"
            )
            
            # Add request information to error monitoring if it was an error
            if response.status_code >= 400:
                current_app.logger.warning(
                    f"Request resulted in {response.status_code} status",
                    extra={
                        'request_id': g.get('request_id'),
                        'path': request.path,
                        'method': request.method,
                        'duration_ms': duration_ms,
                        'status_code': response.status_code,
                        'user_agent': request.user_agent.string if request.user_agent else 'Unknown',
                    }
                )
        
        # Mark request as handled
        g.request_handled = True
        
        return response
    
    @app.teardown_request
    def teardown_request(exception=None):
        """
        Actions to perform after each request, even if an exception occurred
        
        Args:
            exception: Exception raised during request processing, if any
        """
        # Check if the request was handled normally
        if hasattr(g, 'request_handled') and not g.request_handled:
            # Request processing was interrupted by an exception
            current_app.logger.error(
                f"Request {request.method} {request.path} failed with unhandled exception",
                extra={
                    'request_id': g.get('request_id', 'unknown'),
                    'exception': str(exception) if exception else 'Unknown',
                    'traceback': traceback.format_exc() if exception else None
                }
            )


def performance_monitoring(function_name=None):
    """
    Decorator for monitoring function performance
    
    Args:
        function_name (str, optional): Name to use in logs. Defaults to function name.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time()
            result = f(*args, **kwargs)
            duration_ms = (time() - start_time) * 1000
            
            # Log execution time
            name = function_name or f.__name__
            
            # Only log slow operations (> 100ms)
            if duration_ms > 100:
                current_app.logger.info(
                    f"Function {name} executed in {duration_ms:.2f}ms"
                )
            
            return result
        return decorated_function
    
    # Handle both @performance_monitoring and @performance_monitoring('name')
    if callable(function_name):
        f = function_name
        function_name = None
        return decorator(f)
        
    return decorator
