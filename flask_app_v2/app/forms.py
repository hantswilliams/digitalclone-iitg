"""
Form classes for the application
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange, URL
from app.utils.forms import validate_password_strength, validate_username, validate_file_size


class TextForm(FlaskForm):
    """Form for creating text entries"""
    text_content = TextAreaField(
        'Text Content', 
        validators=[
            DataRequired(message="Text content is required"),
            Length(min=10, max=5000, message="Text must be between 10 and 5000 characters")
        ]
    )


class PhotoForm(FlaskForm):
    """Form for uploading photos"""
    file = FileField(
        'Photo',
        validators=[
            FileRequired(message="Please select a photo to upload"),
            FileAllowed(['jpg', 'jpeg', 'png'], message="Only JPG, JPEG, and PNG files are allowed"),
            validate_file_size(max_size_mb=10)
        ]
    )
    description = StringField(
        'Description',
        validators=[
            Optional(),
            Length(max=200, message="Description cannot exceed 200 characters")
        ]
    )


class AudioGenerationForm(FlaskForm):
    """Form for generating audio from text"""
    text_id = IntegerField(
        'Text ID',
        validators=[
            DataRequired(message="Text ID is required")
        ]
    )
    voice = StringField(
        'Voice',
        validators=[
            DataRequired(message="Voice selection is required"),
            Length(max=50, message="Voice name cannot exceed 50 characters")
        ]
    )
    provider = StringField(
        'Provider',
        validators=[
            Optional(),
            Length(max=50, message="Provider name cannot exceed 50 characters")
        ]
    )


class VideoGenerationForm(FlaskForm):
    """Form for generating video from photo and audio"""
    photo_id = IntegerField(
        'Photo ID',
        validators=[
            DataRequired(message="Photo ID is required")
        ]
    )
    audio_id = IntegerField(
        'Audio ID',
        validators=[
            DataRequired(message="Audio ID is required")
        ]
    )
    provider = StringField(
        'Provider',
        validators=[
            Optional(),
            Length(max=50, message="Provider name cannot exceed 50 characters")
        ]
    )
    preprocess = SelectField(
        'Preprocess',
        choices=[
            ('resize', 'Resize'),
            ('crop', 'Crop'),
            ('full', 'Full')
        ],
        default='resize'
    )
    still_mode = BooleanField('Still Mode', default=True)
    use_enhancer = BooleanField('Use Enhancer', default=True)
    pose_style = IntegerField(
        'Pose Style',
        validators=[
            Optional(),
            NumberRange(min=0, max=10, message="Pose style must be between 0 and 10")
        ],
        default=0
    )
    size = IntegerField(
        'Size',
        validators=[
            Optional(),
            NumberRange(min=256, max=1024, message="Size must be between 256 and 1024")
        ],
        default=512
    )
    expression_scale = IntegerField(
        'Expression Scale',
        validators=[
            Optional(),
            NumberRange(min=0, max=2, message="Expression scale must be between 0 and 2")
        ],
        default=1
    )


class PresentationForm(FlaskForm):
    """Form for creating presentations"""
    title = StringField(
        'Title',
        validators=[
            DataRequired(message="Title is required"),
            Length(min=3, max=100, message="Title must be between 3 and 100 characters")
        ]
    )
    videos = StringField(
        'Videos',
        validators=[
            DataRequired(message="At least one video must be selected")
        ]
    )


class ScormPackageForm(FlaskForm):
    """Form for creating SCORM packages"""
    presentation_id = IntegerField(
        'Presentation ID',
        validators=[
            DataRequired(message="Presentation ID is required")
        ]
    )
    title = StringField(
        'Title',
        validators=[
            Optional(),
            Length(min=3, max=100, message="Title must be between 3 and 100 characters")
        ]
    )


class ProjectForm(FlaskForm):
    """Form for creating and editing projects"""
    title = StringField(
        'Project Title', 
        validators=[
            DataRequired(message="Project title is required"),
            Length(min=1, max=100, message="Project title must be between 1 and 100 characters")
        ]
    )
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=500, message="Description cannot exceed 500 characters")
        ]
    )
    thumbnail = FileField(
        'Project Thumbnail',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png'], message="Only JPG, JPEG, and PNG files are allowed"),
            validate_file_size(max_size_mb=5)
        ]
    )


class ProjectMediaForm(FlaskForm):
    """Form for adding or removing media from a project"""
    media_type = SelectField(
        'Media Type',
        choices=[
            ('text', 'Text'),
            ('photo', 'Photo'),
            ('audio', 'Audio'),
            ('video', 'Video'),
            ('powerpoint', 'Presentation')
        ],
        validators=[
            DataRequired(message="Media type is required")
        ]
    )
    media_id = IntegerField(
        'Media ID',
        validators=[
            DataRequired(message="Media ID is required")
        ]
    )
