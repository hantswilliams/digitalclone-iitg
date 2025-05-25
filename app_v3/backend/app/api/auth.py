"""
Authentication API endpoints
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, 
    get_jwt_identity, get_jwt
)
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User, UserRole
from ..schemas import (
    UserRegistrationSchema, UserLoginSchema, UserResponseSchema,
    LoginResponseSchema, MessageResponseSchema, ErrorResponseSchema,
    UserProfileUpdateSchema, ChangePasswordSchema
)
from ..auth import JWTBlocklist

auth_bp = Blueprint('auth', __name__)

# Initialize schemas
registration_schema = UserRegistrationSchema()
login_schema = UserLoginSchema()
user_response_schema = UserResponseSchema()
login_response_schema = LoginResponseSchema()
message_schema = MessageResponseSchema()
error_schema = ErrorResponseSchema()
profile_update_schema = UserProfileUpdateSchema()
change_password_schema = ChangePasswordSchema()


@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Validate request data
        data = registration_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'errors': err.messages
        })), 400
    
    try:
        # Remove confirm_password from data before creating user
        data.pop('confirm_password', None)
        
        # Create new user
        user = User(
            email=data['email'],
            username=data['username'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            department=data.get('department'),
            title=data.get('title'),
            role=UserRole(data.get('role', 'faculty'))
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': 3600  # 1 hour in seconds
        }
        
        return jsonify(login_response_schema.dump(response_data)), 201
        
    except IntegrityError as e:
        db.session.rollback()
        
        # Check which constraint failed
        error_msg = str(e.orig).lower()
        if 'email' in error_msg:
            return jsonify(error_schema.dump({
                'message': 'Email already exists',
                'errors': {'email': ['A user with this email already exists']}
            })), 409
        elif 'username' in error_msg:
            return jsonify(error_schema.dump({
                'message': 'Username already exists', 
                'errors': {'username': ['A user with this username already exists']}
            })), 409
        else:
            return jsonify(error_schema.dump({
                'message': 'Registration failed due to a data conflict'
            })), 409
            
    except Exception as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'message': 'Internal server error during registration'
        })), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        # Validate request data
        data = login_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'errors': err.messages
        })), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify(error_schema.dump({
            'message': 'Invalid email or password'
        })), 401
    
    if not user.is_active:
        return jsonify(error_schema.dump({
            'message': 'Account is deactivated. Please contact support.'
        })), 403
    
    # Create tokens with extended expiry if remember_me is True
    extra_kwargs = {}
    expires_in = 3600  # Default 1 hour
    
    if data.get('remember_me'):
        from datetime import timedelta
        extra_kwargs = {
            'expires_delta': timedelta(days=7)
        }
        expires_in = 7 * 24 * 3600  # 7 days in seconds
    
    access_token = create_access_token(identity=str(user.id), **extra_kwargs)
    refresh_token = create_refresh_token(identity=str(user.id))
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    
    response_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'expires_in': expires_in
    }
    
    return jsonify(login_response_schema.dump(response_data)), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Token refresh endpoint"""
    current_user_id = get_jwt_identity()
    
    # Verify user still exists and is active
    user = User.query.get(current_user_id)
    if not user or not user.is_active:
        return jsonify(error_schema.dump({
            'message': 'User not found or inactive'
        })), 404
    
    # Create new access token
    access_token = create_access_token(identity=current_user_id)
    
    response_data = {
        'access_token': access_token,
        'expires_in': 3600  # 1 hour in seconds
    }
    
    return jsonify(response_data), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint"""
    token = get_jwt()
    jti = token['jti']
    expires_at = token['exp']
    
    # Add token to blocklist
    JWTBlocklist.add_token_to_blocklist(jti, expires_at)
    
    return jsonify(message_schema.dump({
        'message': 'Successfully logged out'
    })), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Get user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify(error_schema.dump({
            'message': 'User not found'
        })), 404
    
    return jsonify(user_response_schema.dump(user.to_dict(include_sensitive=True))), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify(error_schema.dump({
            'message': 'User not found'
        })), 404
    
    try:
        # Validate request data
        data = profile_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'errors': err.messages
        })), 400
    
    # Update user fields
    for field, value in data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    try:
        db.session.commit()
        return jsonify(user_response_schema.dump(user.to_dict())), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'message': 'Failed to update profile'
        })), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify(error_schema.dump({
            'message': 'User not found'
        })), 404
    
    try:
        # Validate request data
        data = change_password_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'errors': err.messages
        })), 400
    
    # Verify current password
    if not user.check_password(data['current_password']):
        return jsonify(error_schema.dump({
            'message': 'Current password is incorrect'
        })), 400
    
    # Set new password
    user.set_password(data['new_password'])
    
    try:
        db.session.commit()
        
        # Revoke all existing tokens for security
        JWTBlocklist.revoke_all_user_tokens(user.id)
        
        return jsonify(message_schema.dump({
            'message': 'Password changed successfully. Please log in again.'
        })), 200
    except Exception as e:
        db.session.rollback()
        return jsonify(error_schema.dump({
            'message': 'Failed to change password'
        })), 500


@auth_bp.route('/verify-token', methods=['POST'])
@jwt_required()
def verify_token():
    """Verify if current token is valid"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify(error_schema.dump({
            'message': 'Invalid token or inactive user'
        })), 401
    
    return jsonify({
        'valid': True,
        'user': user_response_schema.dump(user.to_dict())
    }), 200
