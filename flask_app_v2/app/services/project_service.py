"""
Project service for managing user projects
"""
from flask import current_app
from app.extensions import db
from app.models import Project, ProjectTextAssociation, ProjectPhotoAssociation
from app.models import ProjectAudioAssociation, ProjectVideoAssociation, ProjectPowerpointAssociation


class ProjectService:
    """Service for managing projects and their associations with media"""
    
    def create_project(self, user_id, name, description=""):
        """
        Create a new project for a user
        
        Args:
            user_id (str): ID of the user creating the project
            name (str): Project name
            description (str): Project description
            
        Returns:
            dict: Result containing status and project data
        """
        try:
            project = Project(user_id=user_id, name=name, description=description)
            db.session.add(project)
            db.session.commit()
            
            return {
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'user_id': project.user_id,
                    'created_at': project.created_at.isoformat()
                }
            }
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating project: {str(e)}")
            return {
                'success': False,
                'error': f'Project creation error: {str(e)}'
            }
    
    def get_projects(self, user_id):
        """
        Get all projects for a user
        
        Args:
            user_id (str): ID of the user
            
        Returns:
            dict: Result containing status and list of projects
        """
        try:
            projects = Project.query.filter_by(user_id=user_id).all()
            
            return {
                'success': True,
                'projects': [{
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'user_id': project.user_id,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat()
                } for project in projects]
            }
        
        except Exception as e:
            current_app.logger.error(f"Error getting projects: {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving projects: {str(e)}'
            }
    
    def get_project(self, project_id, user_id=None):
        """
        Get a specific project with all its associated media
        
        Args:
            project_id (int): ID of the project to retrieve
            user_id (str, optional): User ID for authorization check
            
        Returns:
            dict: Result containing status and project details with media
        """
        try:
            query = Project.query.filter_by(id=project_id)
            if user_id:
                query = query.filter_by(user_id=user_id)
                
            project = query.first()
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found or access denied'
                }
            
            # Get all media associated with the project
            return {
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'user_id': project.user_id,
                    'created_at': project.created_at.isoformat(),
                    'updated_at': project.updated_at.isoformat(),
                    'texts': [{
                        'id': text.id,
                        'text_content': text.text_content,
                        'created_at': text.created_at.isoformat()
                    } for text in project.texts],
                    'photos': [{
                        'id': photo.id,
                        'photo_url': photo.photo_url,
                        'photo_description': photo.photo_description,
                        'created_at': photo.created_at.isoformat()
                    } for photo in project.photos],
                    'audios': [{
                        'id': audio.id,
                        'audio_url': audio.audio_url,
                        'audio_text': audio.audio_text,
                        'voice': audio.voice,
                        'created_at': audio.created_at.isoformat()
                    } for audio in project.audios],
                    'videos': [{
                        'id': video.id,
                        'video_url': video.video_url,
                        'video_text': video.video_text,
                        'created_at': video.created_at.isoformat()
                    } for video in project.videos],
                    'powerpoints': [{
                        'id': ppt.id,
                        'title': ppt.title,
                        'ppt_url': ppt.ppt_url,
                        'created_at': ppt.created_at.isoformat()
                    } for ppt in project.powerpoints]
                }
            }
        
        except Exception as e:
            current_app.logger.error(f"Error getting project: {str(e)}")
            return {
                'success': False,
                'error': f'Error retrieving project: {str(e)}'
            }
    
    def update_project(self, project_id, user_id, data):
        """
        Update project details
        
        Args:
            project_id (int): ID of the project to update
            user_id (str): User ID for authorization
            data (dict): Data to update (name, description)
            
        Returns:
            dict: Result containing status and updated project
        """
        try:
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found or access denied'
                }
            
            if 'name' in data:
                project.name = data['name']
            
            if 'description' in data:
                project.description = data['description']
            
            db.session.commit()
            
            return {
                'success': True,
                'project': {
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'user_id': project.user_id,
                    'updated_at': project.updated_at.isoformat()
                }
            }
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating project: {str(e)}")
            return {
                'success': False,
                'error': f'Project update error: {str(e)}'
            }
    
    def delete_project(self, project_id, user_id):
        """
        Delete a project
        
        Args:
            project_id (int): ID of the project to delete
            user_id (str): User ID for authorization
            
        Returns:
            dict: Result containing status
        """
        try:
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found or access denied'
                }
            
            db.session.delete(project)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Project {project_id} deleted successfully'
            }
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting project: {str(e)}")
            return {
                'success': False,
                'error': f'Project deletion error: {str(e)}'
            }
    
    def add_to_project(self, project_id, user_id, media_type, media_id):
        """
        Add a media item to a project
        
        Args:
            project_id (int): ID of the project
            user_id (str): User ID for authorization
            media_type (str): Type of media ('text', 'photo', 'audio', 'video', 'powerpoint')
            media_id (int): ID of the media item
            
        Returns:
            dict: Result containing status
        """
        try:
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found or access denied'
                }
            
            # Add association based on media type
            if media_type == 'text':
                association = ProjectTextAssociation(project_id=project_id, text_id=media_id)
            elif media_type == 'photo':
                association = ProjectPhotoAssociation(project_id=project_id, photo_id=media_id)
            elif media_type == 'audio':
                association = ProjectAudioAssociation(project_id=project_id, audio_id=media_id)
            elif media_type == 'video':
                association = ProjectVideoAssociation(project_id=project_id, video_id=media_id)
            elif media_type == 'powerpoint':
                association = ProjectPowerpointAssociation(project_id=project_id, powerpoint_id=media_id)
            else:
                return {
                    'success': False,
                    'error': f'Invalid media type: {media_type}'
                }
            
            db.session.add(association)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{media_type.capitalize()} added to project successfully'
            }
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding to project: {str(e)}")
            return {
                'success': False,
                'error': f'Error adding to project: {str(e)}'
            }
    
    def remove_from_project(self, project_id, user_id, media_type, media_id):
        """
        Remove a media item from a project
        
        Args:
            project_id (int): ID of the project
            user_id (str): User ID for authorization
            media_type (str): Type of media ('text', 'photo', 'audio', 'video', 'powerpoint')
            media_id (int): ID of the media item
            
        Returns:
            dict: Result containing status
        """
        try:
            project = Project.query.filter_by(id=project_id, user_id=user_id).first()
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found or access denied'
                }
            
            # Remove association based on media type
            if media_type == 'text':
                association = ProjectTextAssociation.query.filter_by(
                    project_id=project_id, text_id=media_id).first()
            elif media_type == 'photo':
                association = ProjectPhotoAssociation.query.filter_by(
                    project_id=project_id, photo_id=media_id).first()
            elif media_type == 'audio':
                association = ProjectAudioAssociation.query.filter_by(
                    project_id=project_id, audio_id=media_id).first()
            elif media_type == 'video':
                association = ProjectVideoAssociation.query.filter_by(
                    project_id=project_id, video_id=media_id).first()
            elif media_type == 'powerpoint':
                association = ProjectPowerpointAssociation.query.filter_by(
                    project_id=project_id, powerpoint_id=media_id).first()
            else:
                return {
                    'success': False,
                    'error': f'Invalid media type: {media_type}'
                }
            
            if not association:
                return {
                    'success': False,
                    'error': f'{media_type.capitalize()} not found in project'
                }
            
            db.session.delete(association)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{media_type.capitalize()} removed from project successfully'
            }
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error removing from project: {str(e)}")
            return {
                'success': False,
                'error': f'Error removing from project: {str(e)}'
            }
