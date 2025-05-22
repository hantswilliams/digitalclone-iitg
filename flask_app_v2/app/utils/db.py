"""
Database error handling utilities
"""
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError
from app.errors import APIError
from app.extensions import db
from functools import wraps
import traceback


def handle_db_error(f):
    """
    Decorator for handling database errors
    
    Args:
        f: Function to wrap
        
    Returns:
        wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except IntegrityError as e:
            db.session.rollback()
            
            # Check for specific integrity errors
            error_msg = str(e.orig)
            
            if 'unique constraint' in error_msg.lower():
                # Handle duplicate entry errors
                if 'username' in error_msg.lower():
                    raise APIError('Username already exists', 409)
                elif 'email' in error_msg.lower():
                    raise APIError('Email address already in use', 409)
                else:
                    raise APIError('A duplicate entry was detected', 409)
            elif 'foreign key constraint' in error_msg.lower():
                # Handle reference errors
                raise APIError('Referenced resource does not exist', 400)
            else:
                # Generic integrity error
                current_app.logger.error(f"Database integrity error: {str(e)}")
                raise APIError('Database integrity error', 400)
                
        except DataError as e:
            db.session.rollback()
            current_app.logger.error(f"Database data error: {str(e)}")
            
            # Check for specific data errors
            error_msg = str(e.orig)
            
            if 'out of range' in error_msg.lower():
                raise APIError('Data value out of range', 400)
            elif 'invalid input syntax' in error_msg.lower():
                raise APIError('Invalid data format', 400)
            else:
                raise APIError('Invalid data provided', 400)
                
        except SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(e)}")
            current_app.logger.debug(traceback.format_exc())
            
            raise APIError('A database error occurred', 500)
            
    return decorated_function


class DBErrorContext:
    """
    Context manager for handling database errors
    
    Example:
        with DBErrorContext('Error updating user profile'):
            user.name = new_name
            db.session.commit()
    """
    
    def __init__(self, error_message=None, status_code=500):
        """
        Initialize with custom error message and status code
        
        Args:
            error_message (str): Custom error message to use
            status_code (int): HTTP status code to use for errors
        """
        self.error_message = error_message or 'A database error occurred'
        self.status_code = status_code
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception occurred
            return False
            
        # Handle database-related exceptions
        if issubclass(exc_type, IntegrityError):
            db.session.rollback()
            
            # Parse the error for better messages
            error_msg = str(exc_val)
            if 'unique constraint' in error_msg.lower():
                raise APIError('A duplicate entry was detected', 409)
            elif 'foreign key constraint' in error_msg.lower():
                raise APIError('Referenced resource does not exist', 400)
            else:
                current_app.logger.error(f"Database integrity error: {error_msg}")
                raise APIError(self.error_message, self.status_code)
                
        elif issubclass(exc_type, DataError):
            db.session.rollback()
            current_app.logger.error(f"Database data error: {str(exc_val)}")
            raise APIError('Invalid data provided', 400)
            
        elif issubclass(exc_type, SQLAlchemyError):
            db.session.rollback()
            current_app.logger.error(f"Database error: {str(exc_val)}")
            raise APIError(self.error_message, self.status_code)
            
        # Re-raise other exceptions
        return False
