"""
Form handling utilities and validators
"""
from flask import current_app
from wtforms.validators import ValidationError
import re


class FormHandler:
    """
    Helper class for form handling with standardized validation and error responses
    """
    
    def __init__(self, form_class):
        """
        Initialize with a WTForms form class
        
        Args:
            form_class: WTForms Form class
        """
        self.form_class = form_class
        self.form = None
        self.errors = {}
    
    def validate(self, request, extra_validators=None):
        """
        Validate form data from request
        
        Args:
            request: Flask request object
            extra_validators: Additional validation functions
            
        Returns:
            bool: Whether validation passed
        """
        # Create form instance from request data
        if request.is_json:
            self.form = self.form_class.from_json(request.json)
        else:
            self.form = self.form_class(request.form)
        
        # Run WTForms validation
        valid = self.form.validate()
        
        # Apply any extra validators
        if valid and extra_validators:
            for validator in extra_validators:
                try:
                    validator(self.form)
                except ValidationError as e:
                    field_name = getattr(e, 'field_name', None) or 'general'
                    if not hasattr(self.form, '_errors'):
                        self.form._errors = {}
                    if field_name not in self.form._errors:
                        self.form._errors[field_name] = []
                    self.form._errors[field_name].append(str(e))
                    valid = False
        
        # Collect all errors
        if not valid:
            self.errors = {}
            
            # Field-specific errors
            for field_name, field in self.form._fields.items():
                if field.errors:
                    self.errors[field_name] = field.errors[0]  # Just take the first error
            
            # Form-level errors
            if hasattr(self.form, '_errors'):
                for field_name, errors in self.form._errors.items():
                    if field_name not in self.errors:
                        self.errors[field_name] = errors[0]
        
        return valid
    
    def get_data(self):
        """
        Get cleaned form data
        
        Returns:
            dict: Cleaned form data
        """
        if not self.form:
            return {}
        
        # Extract data from the form
        result = {}
        for field_name, field in self.form._fields.items():
            # Skip CSRF token field
            if field_name == 'csrf_token':
                continue
            
            result[field_name] = field.data
        
        return result
    
    def get_errors(self):
        """
        Get validation errors
        
        Returns:
            dict: Field errors
        """
        return self.errors


# Common validator functions
def validate_password_strength(form, field):
    """
    Validate password strength
    
    Args:
        form: WTForms form
        field: Password field
    """
    password = field.data
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        raise ValidationError("Password must contain at least one number")
    
    if not re.search(r'[^A-Za-z0-9]', password):
        raise ValidationError("Password must contain at least one special character")


def validate_username(form, field):
    """
    Validate username format
    
    Args:
        form: WTForms form
        field: Username field
    """
    username = field.data
    
    if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', username):
        raise ValidationError("Username must be 3-20 characters and contain only letters, numbers, underscores, and hyphens")


def validate_file_size(max_size_mb=5):
    """
    Factory function to create file size validator
    
    Args:
        max_size_mb: Maximum file size in MB
        
    Returns:
        function: Validator function
    """
    max_bytes = max_size_mb * 1024 * 1024
    
    def _validator(form, field):
        if field.data is None:
            return
        
        file_data = field.data
        if hasattr(file_data, 'content_length'):
            file_size = file_data.content_length
        elif hasattr(file_data, 'size'):
            file_size = file_data.size
        else:
            # Can't determine size, assume it's valid
            current_app.logger.warning("Could not determine file size for validation")
            return
            
        if file_size > max_bytes:
            raise ValidationError(f"File size must not exceed {max_size_mb}MB")
    
    return _validator
