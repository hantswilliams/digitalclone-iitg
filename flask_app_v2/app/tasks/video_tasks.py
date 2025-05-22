"""
Celery tasks for video processing
"""
from app.extensions import celery, db
from app.services.video_service import VideoService
from app.models import Photo, Audio, Video
from flask import current_app


@celery.task(bind=True)
def generate_video_task(self, photo_id, audio_id, provider='sadtalker', user_id=None, **kwargs):
    """
    Celery task to generate talking head video
    
    Args:
        photo_id (int): ID of the photo to use
        audio_id (int): ID of the audio to use
        provider (str): Video generator provider to use
        user_id (str, optional): User ID for tracking
        **kwargs: Additional parameters for the video generator
        
    Returns:
        dict: Result of video generation
    """
    try:
        with current_app.app_context():
            # Get the photo and audio from database
            photo = Photo.query.get(photo_id)
            audio = Audio.query.get(audio_id)
            
            if not photo:
                return {
                    'success': False,
                    'error': f'Photo with ID {photo_id} not found'
                }
                
            if not audio:
                return {
                    'success': False,
                    'error': f'Audio with ID {audio_id} not found'
                }
            
            # Update task state
            self.update_state(state='PROCESSING', meta={
                'status': 'Generating video',
                'photo_id': photo_id,
                'audio_id': audio_id
            })
            
            # Initialize service and generate video
            video_service = VideoService()
            result = video_service.generate_video(
                photo.photo_url, 
                audio.audio_url,
                provider,
                **kwargs
            )
            
            if not result['success']:
                return result
            
            # Save the video in the database
            video = Video(
                user_id=user_id or photo.user_id,
                photo_id=photo_id,
                audio_id=audio_id,
                video_url=result['url'],
                video_text=audio.audio_text if hasattr(audio, 'audio_text') else None
            )
            
            db.session.add(video)
            db.session.commit()
            
            # Add the video ID to the result
            result['video_id'] = video.id
            
            return result
            
    except Exception as e:
        current_app.logger.error(f"Error in generate_video_task: {str(e)}")
        return {
            'success': False,
            'error': f'Video generation task error: {str(e)}'
        }
