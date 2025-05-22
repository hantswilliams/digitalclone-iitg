"""
Celery tasks for audio processing
"""
from app.extensions import celery, db
from app.services.audio_service import AudioService
from app.models import Text, Audio
from flask import current_app


@celery.task(bind=True)
def generate_audio_task(self, text_id, voice, provider='playht', user_id=None):
    """
    Celery task to generate audio from text
    
    Args:
        text_id (int): ID of the text to convert
        voice (str): Voice identifier to use
        provider (str): TTS provider to use
        user_id (str, optional): User ID for tracking
        
    Returns:
        dict: Result of audio generation
    """
    try:
        with current_app.app_context():
            # Get the text from database
            text_record = Text.query.get(text_id)
            if not text_record:
                return {
                    'success': False,
                    'error': f'Text with ID {text_id} not found'
                }
            
            text_content = text_record.text_content
            
            # Update task state
            self.update_state(state='PROCESSING', meta={
                'status': 'Generating audio',
                'text_id': text_id,
                'voice': voice
            })
            
            # Initialize service and generate audio
            audio_service = AudioService()
            result = audio_service.generate_audio(text_content, voice, provider)
            
            if not result['success']:
                return result
            
            # Save the audio in the database
            audio = Audio(
                user_id=user_id or text_record.user_id,
                text_id=text_id,
                audio_url=result['url'],
                audio_text=text_content,
                voice=voice
            )
            
            db.session.add(audio)
            db.session.commit()
            
            # Add the audio ID to the result
            result['audio_id'] = audio.id
            
            return result
            
    except Exception as e:
        current_app.logger.error(f"Error in generate_audio_task: {str(e)}")
        return {
            'success': False,
            'error': f'Audio generation task error: {str(e)}'
        }
