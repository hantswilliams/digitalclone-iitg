"""
Database models for the application
"""
from app.extensions import db
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
import datetime


class User(UserMixin, db.Model):
    """User model for authentication and tracking ownership of resources"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True)
    username = Column(String, unique=True, nullable=True)  # For basic auth
    password = Column(String, nullable=True)  # For basic auth
    email = Column(String, unique=True)
    name = Column(String)
    profile = Column(String)
    permissions = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    def get_id(self):
        """Return the user_id as a unicode string"""
        return str(self.user_id)
    
    # Relationships
    texts = relationship('Text', backref='user', lazy=True)
    photos = relationship('Photo', backref='user', lazy=True)
    projects = relationship('Project', backref='user', lazy=True)
    
    def get_id(self):
        """Return the user_id as a unicode string"""
        return str(self.user_id)


class Text(db.Model):
    """Text content that can be used for audio generation"""
    __tablename__ = 'text'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    text_content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Many-to-many relationship with Project
    projects = relationship('Project', secondary='project_text_association', back_populates='texts')


class Photo(db.Model):
    """Photo/Image that can be used for video generation"""
    __tablename__ = 'photo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    photo_url = Column(String)
    photo_description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Many-to-many relationship with Project
    projects = relationship('Project', secondary='project_photo_association', back_populates='photos')


class Audio(db.Model):
    """Audio generated from text using TTS services"""
    __tablename__ = 'audio'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    text_id = Column(Integer, ForeignKey('text.id'), nullable=False)
    audio_url = Column(String)
    audio_text = Column(String)
    voice = Column(String)
    cloned_voice_id = Column(Integer, ForeignKey('cloned_voice.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationship to Text
    text = relationship('Text', backref=backref('audios', lazy=True))
    
    # Relationship to ClonedVoice (optional)
    cloned_voice = relationship('ClonedVoice', backref=backref('audios', lazy=True))
    
    # Many-to-many relationship with Project
    projects = relationship('Project', secondary='project_audio_association', back_populates='audios')


class Video(db.Model):
    """Video generated from photo and audio"""
    __tablename__ = 'video'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    photo_id = Column(Integer, ForeignKey('photo.id'))
    audio_id = Column(Integer, ForeignKey('audio.id'))
    video_url = Column(String)
    video_text = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    photo = relationship('Photo', backref=backref('videos', lazy=True))
    audio = relationship('Audio', backref=backref('videos', lazy=True))
    
    # Many-to-many relationship with Project
    projects = relationship('Project', secondary='project_video_association', back_populates='videos')


class PowerPoint(db.Model):
    """PowerPoint presentation generated from videos and text"""
    __tablename__ = 'powerpoint'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    title = Column(String)
    ppt_url = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Many-to-many relationship with Project
    projects = relationship('Project', secondary='project_powerpoint_association', back_populates='powerpoints')


class Project(db.Model):
    """Project to organize content (texts, photos, audios, videos, powerpoints)"""
    __tablename__ = 'project'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    name = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Many-to-many relationships
    texts = relationship('Text', secondary='project_text_association', back_populates='projects')
    photos = relationship('Photo', secondary='project_photo_association', back_populates='projects')
    audios = relationship('Audio', secondary='project_audio_association', back_populates='projects')
    videos = relationship('Video', secondary='project_video_association', back_populates='projects')
    powerpoints = relationship('PowerPoint', secondary='project_powerpoint_association', back_populates='projects')


class ClonedVoice(db.Model):
    """User's cloned voice profile for personalized TTS"""
    __tablename__ = 'cloned_voice'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.user_id'))
    voice_name = Column(String)
    voice_id = Column(String, unique=True)  # Provider's voice ID
    provider = Column(String)  # 'playht', 'elevenlabs', 'internal'
    voice_type = Column(String)  # 'natural', 'expressive', 'narrator', etc.
    status = Column(String)  # 'processing', 'ready', 'failed'
    sample_url = Column(String, nullable=True)  # URL to a sample of the voice
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationship to User
    user = relationship('User', backref=backref('cloned_voices', lazy=True))


# Association tables for many-to-many relationships
class ProjectTextAssociation(db.Model):
    __tablename__ = 'project_text_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    text_id = Column(Integer, ForeignKey('text.id'), primary_key=True)


class ProjectPhotoAssociation(db.Model):
    __tablename__ = 'project_photo_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    photo_id = Column(Integer, ForeignKey('photo.id'), primary_key=True)


class ProjectAudioAssociation(db.Model):
    __tablename__ = 'project_audio_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    audio_id = Column(Integer, ForeignKey('audio.id'), primary_key=True)


class ProjectVideoAssociation(db.Model):
    __tablename__ = 'project_video_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    video_id = Column(Integer, ForeignKey('video.id'), primary_key=True)


class ProjectPowerpointAssociation(db.Model):
    __tablename__ = 'project_powerpoint_association'
    project_id = Column(Integer, ForeignKey('project.id'), primary_key=True)
    powerpoint_id = Column(Integer, ForeignKey('powerpoint.id'), primary_key=True)
