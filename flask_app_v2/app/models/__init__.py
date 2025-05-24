"""
Models package initialization
"""
# Import models to make them available when importing from the models package
from app.models.models import (
    User, Text, Photo, Audio, Video, PowerPoint, Project, ClonedVoice,
    ProjectTextAssociation, ProjectPhotoAssociation, ProjectAudioAssociation,
    ProjectVideoAssociation, ProjectPowerpointAssociation
)
