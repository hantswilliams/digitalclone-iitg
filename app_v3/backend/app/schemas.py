"""
Marshmallow schemas for request/response validation and serialization
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError
import re


class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    email = fields.Email(required=True, validate=validate.Length(max=120))
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_password = fields.Str(required=True)
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    department = fields.Str(allow_none=True, validate=validate.Length(max=100))
    title = fields.Str(allow_none=True, validate=validate.Length(max=100))
    role = fields.Str(load_default='faculty', validate=validate.OneOf(['admin', 'faculty', 'student']))

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that password and confirm_password match"""
        if data.get('password') != data.get('confirm_password'):
            raise ValidationError('Passwords do not match', 'confirm_password')

    @validates_schema  
    def validate_username_format(self, data, **kwargs):
        """Validate username format - alphanumeric and underscores only"""
        username = data.get('username', '')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Username can only contain letters, numbers, and underscores', 'username')

    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validate password strength"""
        password = data.get('password', '')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter', 'password')
        
        # Check for at least one lowercase letter  
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter', 'password')
            
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit', 'password')


class UserLoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(load_default=False)


class TokenRefreshSchema(Schema):
    """Schema for token refresh - JWT handles this automatically but useful for docs"""
    pass


class UserProfileUpdateSchema(Schema):
    """Schema for updating user profile"""
    first_name = fields.Str(validate=validate.Length(min=1, max=50))
    last_name = fields.Str(validate=validate.Length(min=1, max=50))
    department = fields.Str(allow_none=True, validate=validate.Length(max=100))
    title = fields.Str(allow_none=True, validate=validate.Length(max=100))


class ChangePasswordSchema(Schema):
    """Schema for changing password"""
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_new_password = fields.Str(required=True)

    @validates_schema
    def validate_passwords_match(self, data, **kwargs):
        """Validate that new_password and confirm_new_password match"""
        if data.get('new_password') != data.get('confirm_new_password'):
            raise ValidationError('New passwords do not match', 'confirm_new_password')

    @validates_schema
    def validate_password_strength(self, data, **kwargs):
        """Validate new password strength"""
        password = data.get('new_password', '')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Password must contain at least one uppercase letter', 'new_password')
        
        # Check for at least one lowercase letter  
        if not re.search(r'[a-z]', password):
            raise ValidationError('Password must contain at least one lowercase letter', 'new_password')
            
        # Check for at least one digit
        if not re.search(r'\d', password):
            raise ValidationError('Password must contain at least one digit', 'new_password')


class UserResponseSchema(Schema):
    """Schema for user response data"""
    id = fields.Int()
    email = fields.Email()
    username = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()
    full_name = fields.Str()
    department = fields.Str(allow_none=True)
    title = fields.Str(allow_none=True)
    role = fields.Str()
    is_active = fields.Bool()
    is_verified = fields.Bool()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    last_login = fields.DateTime(allow_none=True)


class LoginResponseSchema(Schema):
    """Schema for login response"""
    access_token = fields.Str()
    refresh_token = fields.Str()
    user = fields.Nested(UserResponseSchema)
    expires_in = fields.Int()


class MessageResponseSchema(Schema):
    """Schema for simple message responses"""
    message = fields.Str()
    success = fields.Bool(load_default=True)


class ErrorResponseSchema(Schema):
    """Schema for error responses"""
    message = fields.Str()
    errors = fields.Dict(allow_none=True)
    success = fields.Bool(load_default=False)


class AssetUploadSchema(Schema):
    """Schema for asset upload validation"""
    asset_type = fields.Str(required=True, validate=validate.OneOf([
        'portrait', 'voice_sample', 'script'
    ]))
    description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    

class AssetResponseSchema(Schema):
    """Schema for asset response data"""
    id = fields.Int()
    filename = fields.Str()
    original_filename = fields.Str()
    file_size = fields.Int()
    mime_type = fields.Str()
    file_extension = fields.Str()
    asset_type = fields.Str()
    status = fields.Str()
    asset_metadata = fields.Dict(allow_none=True)
    processing_info = fields.Dict(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    download_url = fields.Str(allow_none=True)
    preview_url = fields.Str(allow_none=True)


class AssetListSchema(Schema):
    """Schema for asset list query parameters"""
    asset_type = fields.Str(validate=validate.OneOf([
        'portrait', 'voice_sample', 'script', 'generated_audio', 'generated_video'
    ]))
    status = fields.Str(validate=validate.OneOf([
        'uploading', 'processing', 'ready', 'error', 'deleted'
    ]))
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    per_page = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))


class PresignedUrlSchema(Schema):
    """Schema for presigned URL request"""
    filename = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    asset_type = fields.Str(required=True, validate=validate.OneOf([
        'portrait', 'voice_sample', 'script'
    ]))
    file_size = fields.Int(required=True, validate=validate.Range(min=1))
    content_type = fields.Str(required=True, validate=validate.Length(max=100))


class PresignedUrlResponseSchema(Schema):
    """Schema for presigned URL response"""
    upload_url = fields.Str()
    upload_fields = fields.Dict()
    asset_id = fields.Int()
    expires_in = fields.Int()


# Pagination Schema

class PaginationSchema(Schema):
    """Schema for pagination metadata"""
    page = fields.Int()
    pages = fields.Int()
    per_page = fields.Int()
    total = fields.Int()
    has_next = fields.Bool()
    has_prev = fields.Bool()


# Job Management Schemas

class JobCreateSchema(Schema):
    """Schema for creating a new job"""
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True, validate=validate.Length(max=1000))
    job_type = fields.Str(required=True, validate=validate.OneOf([
        'voice_clone', 'text_to_speech', 'video_generation', 'full_pipeline', 'script_generation'
    ]))
    priority = fields.Str(load_default='normal', validate=validate.OneOf([
        'low', 'normal', 'high', 'urgent'
    ]))
    parameters = fields.Dict(load_default=dict)
    asset_ids = fields.List(fields.Int(), load_default=list)
    estimated_duration = fields.Int(allow_none=True, validate=validate.Range(min=1))


class JobUpdateSchema(Schema):
    """Schema for updating an existing job"""
    title = fields.Str(validate=validate.Length(min=1, max=200))
    description = fields.Str(allow_none=True, validate=validate.Length(max=1000))
    priority = fields.Str(validate=validate.OneOf([
        'low', 'normal', 'high', 'urgent'
    ]))
    parameters = fields.Dict()


class JobStepSchema(Schema):
    """Schema for job step details"""
    id = fields.Int(dump_only=True)
    name = fields.Str()
    description = fields.Str(allow_none=True)
    step_order = fields.Int()
    status = fields.Str()
    progress_percentage = fields.Int()
    started_at = fields.DateTime(allow_none=True, format='iso')
    completed_at = fields.DateTime(allow_none=True, format='iso')
    duration = fields.Float(allow_none=True)
    estimated_duration = fields.Int(allow_none=True)
    input_data = fields.Dict(allow_none=True)
    output_data = fields.Dict(allow_none=True)
    error_info = fields.Dict(allow_none=True)
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')


class JobResponseSchema(Schema):
    """Schema for job response"""
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str(allow_none=True)
    job_type = fields.Str()
    status = fields.Str()
    priority = fields.Str()
    progress_percentage = fields.Int()
    celery_task_id = fields.Str(allow_none=True)
    created_at = fields.DateTime(format='iso')
    updated_at = fields.DateTime(format='iso')
    started_at = fields.DateTime(allow_none=True, format='iso')
    completed_at = fields.DateTime(allow_none=True, format='iso')
    duration = fields.Float(allow_none=True)
    estimated_duration = fields.Int(allow_none=True)
    parameters = fields.Dict(allow_none=True)
    results = fields.Dict(allow_none=True)
    error_info = fields.Dict(allow_none=True)
    asset_ids = fields.List(fields.Int(), dump_default=list)
    output_video_id = fields.Int(allow_none=True)
    steps = fields.List(fields.Nested(JobStepSchema), dump_default=list)


class JobListSchema(Schema):
    """Schema for job list response"""
    jobs = fields.List(fields.Nested(JobResponseSchema))
    pagination = fields.Nested(PaginationSchema)


class JobProgressUpdateSchema(Schema):
    """Schema for updating job progress"""
    progress_percentage = fields.Int(required=True, validate=validate.Range(min=0, max=100))
    message = fields.Str(allow_none=True, validate=validate.Length(max=500))


class JobStepCreateSchema(Schema):
    """Schema for creating a job step"""
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True, validate=validate.Length(max=500))
    step_order = fields.Int(load_default=0)
    estimated_duration = fields.Int(allow_none=True, validate=validate.Range(min=1))
    input_data = fields.Dict(load_default=dict)
