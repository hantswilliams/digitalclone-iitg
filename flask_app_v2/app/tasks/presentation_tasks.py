"""
Celery tasks for presentation processing
"""
from app.extensions import celery, db
from app.services.presentation_service import PresentationService
from app.models import Video, PowerPoint, Text
from flask import current_app


@celery.task(bind=True)
def create_presentation_task(self, title, slides_data, user_id=None):
    """
    Celery task to create a presentation from slides data
    
    Args:
        title (str): Presentation title
        slides_data (list): List of slide data (text, video, images)
        user_id (str, optional): User ID for tracking
        
    Returns:
        dict: Result of presentation creation
    """
    try:
        with current_app.app_context():
            # Update task state
            self.update_state(state='PROCESSING', meta={
                'status': 'Creating presentation',
                'title': title
            })
            
            # Initialize service and create presentation
            presentation_service = PresentationService()
            result = presentation_service.create_presentation(title, slides_data)
            
            if not result['success']:
                return result
            
            # Save the presentation in the database
            ppt = PowerPoint(
                user_id=user_id,
                title=title,
                ppt_url=result['url']
            )
            
            db.session.add(ppt)
            db.session.commit()
            
            # Add the presentation ID to the result
            result['powerpoint_id'] = ppt.id
            
            return result
            
    except Exception as e:
        current_app.logger.error(f"Error in create_presentation_task: {str(e)}")
        return {
            'success': False,
            'error': f'Presentation creation task error: {str(e)}'
        }


@celery.task(bind=True)
def create_scorm_task(self, presentation_id, title=None, metadata=None, user_id=None):
    """
    Celery task to create a SCORM package from a presentation
    
    Args:
        presentation_id (int): ID of the presentation
        title (str, optional): Title for the SCORM package
        metadata (dict, optional): Metadata for the SCORM package
        user_id (str, optional): User ID for tracking
        
    Returns:
        dict: Result of SCORM package creation
    """
    try:
        with current_app.app_context():
            # Get the presentation from database
            ppt = PowerPoint.query.get(presentation_id)
            
            if not ppt:
                return {
                    'success': False,
                    'error': f'Presentation with ID {presentation_id} not found'
                }
            
            # Use presentation title if not provided
            title = title or ppt.title
            
            # Update task state
            self.update_state(state='PROCESSING', meta={
                'status': 'Creating SCORM package',
                'presentation_id': presentation_id,
                'title': title
            })
            
            # Initialize service and create SCORM package
            presentation_service = PresentationService()
            result = presentation_service.create_scorm_package(
                ppt.ppt_url,
                title,
                metadata
            )
            
            return result
            
    except Exception as e:
        current_app.logger.error(f"Error in create_scorm_task: {str(e)}")
        return {
            'success': False,
            'error': f'SCORM creation task error: {str(e)}'
        }
