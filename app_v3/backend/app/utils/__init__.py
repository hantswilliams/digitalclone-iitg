"""
Utility functions for the Voice-Cloned Talking-Head Lecturer application
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError
from ..models import User, UserRole
from ..schemas import ErrorResponseSchema


def handle_errors(f):
    """Decorator to handle common API errors"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify(ErrorResponseSchema().dump({
                'message': 'Validation error',
                'errors': e.messages
            })), 400
        except Exception as e:
            return jsonify(ErrorResponseSchema().dump({
                'message': f'Internal server error: {str(e)}'
            })), 500
    return decorated_function


def require_role(required_role):
    """Decorator to require specific user role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify(ErrorResponseSchema().dump({
                    'message': 'User not found'
                })), 404
            
            if isinstance(required_role, str):
                required_role_enum = UserRole(required_role)
            else:
                required_role_enum = required_role
            
            if user.role != required_role_enum:
                return jsonify(ErrorResponseSchema().dump({
                    'message': f'Access denied. Required role: {required_role_enum.value}'
                })), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_admin(f):
    """Decorator to require admin role"""
    return require_role(UserRole.ADMIN)(f)


def require_faculty_or_admin(f):
    """Decorator to require faculty or admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify(ErrorResponseSchema().dump({
                'message': 'User not found'
            })), 404
        
        if user.role not in [UserRole.FACULTY, UserRole.ADMIN]:
            return jsonify(ErrorResponseSchema().dump({
                'message': 'Access denied. Faculty or admin role required.'
            })), 403
        
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    """Get current authenticated user"""
    current_user_id = get_jwt_identity()
    if current_user_id:
        return User.query.get(current_user_id)
    return None


def validate_file_extension(filename, allowed_extensions):
    """Validate file extension"""
    if not filename:
        return False
    
    # Get file extension
    if '.' not in filename:
        return False
    
    extension = '.' + filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def generate_unique_filename(original_filename, user_id, prefix=''):
    """Generate unique filename for uploads"""
    import uuid
    from datetime import datetime
    
    # Get file extension
    if '.' in original_filename:
        name, extension = original_filename.rsplit('.', 1)
        extension = '.' + extension.lower()
    else:
        extension = ''
    
    # Generate unique filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{user_id}_{timestamp}_{unique_id}{extension}"
    else:
        return f"{user_id}_{timestamp}_{unique_id}{extension}"


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def calculate_audio_duration(file_path):
    """Calculate audio file duration (placeholder for now)"""
    # TODO: Implement using librosa or similar
    # For now, return a placeholder
    return 0.0


def validate_audio_format(file_path):
    """Validate audio file format (placeholder for now)"""
    # TODO: Implement proper audio validation
    # For now, return True
    return True
