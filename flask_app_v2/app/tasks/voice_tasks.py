"""
Celery tasks for voice cloning
"""
import os
from app.extensions import celery, db
from app.services.voice_clone_service import VoiceCloneService
from app.models import ClonedVoice, User
from flask import current_app


@celery.task(bind=True)
def clone_voice_task(self, audio_file_paths, voice_name, voice_type, provider, user_id):
    """
    Celery task to clone a voice
    
    Args:
        audio_file_paths (list): List of audio file paths to use for voice cloning
        voice_name (str): Name to assign to the cloned voice
        voice_type (str): Type of voice to create (natural, expressive, etc.)
        provider (str): Voice cloning provider to use
        user_id (str): User ID for tracking and ownership
        
    Returns:
        dict: Result of voice cloning operation
    """
    try:
        with current_app.app_context():
            # Update task state
            self.update_state(state='PROCESSING', meta={
                'status': 'Cloning voice',
                'voice_name': voice_name,
                'provider': provider
            })
            
            # Initialize service and clone voice
            voice_service = VoiceCloneService()
            result = voice_service.clone_voice(audio_file_paths, voice_name, voice_type, provider)
            
            if not result['success']:
                return result
            
            # Create a new cloned voice record
            cloned_voice = ClonedVoice(
                user_id=user_id,
                voice_name=voice_name,
                voice_id=result['voice_id'],
                provider=provider,
                voice_type=voice_type,
                status='processing'  # Initially set to processing
            )
            
            db.session.add(cloned_voice)
            db.session.commit()
            
            # Add the cloned voice ID to the result
            result['cloned_voice_id'] = cloned_voice.id
            
            return result
            
    except Exception as e:
        current_app.logger.error(f"Error in clone_voice_task: {str(e)}")
        return {
            'success': False,
            'error': f'Voice cloning task error: {str(e)}'
        }


@celery.task(bind=True)
def update_voice_status_task(self, cloned_voice_id, interval=60, max_checks=30):
    """
    Task to periodically check the status of a voice cloning operation
    
    Args:
        cloned_voice_id (int): ID of the cloned voice record to check
        interval (int): Time in seconds between checks
        max_checks (int): Maximum number of status checks before giving up
        
    Returns:
        dict: Final status of the voice cloning operation
    """
    import time
    
    try:
        with current_app.app_context():
            checks = 0
            while checks < max_checks:
                # Get the cloned voice record
                cloned_voice = ClonedVoice.query.get(cloned_voice_id)
                if not cloned_voice:
                    return {
                        'success': False,
                        'error': f'Cloned voice with ID {cloned_voice_id} not found'
                    }
                
                # If already completed, return status
                if cloned_voice.status in ['ready', 'failed']:
                    return {
                        'success': cloned_voice.status == 'ready',
                        'status': cloned_voice.status,
                        'cloned_voice_id': cloned_voice.id,
                        'voice_name': cloned_voice.voice_name
                    }
                
                # In a real implementation, we would check with the provider's API
                # For now, after a few checks, simulate success
                if checks >= 3:  # After 3 checks, mark as ready
                    cloned_voice.status = 'ready'
                    cloned_voice.sample_url = f"/static/samples/voice_{cloned_voice.id}.mp3"
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'status': 'ready',
                        'cloned_voice_id': cloned_voice.id,
                        'voice_name': cloned_voice.voice_name,
                        'sample_url': cloned_voice.sample_url
                    }
                
                # Update task state
                self.update_state(state='PROCESSING', meta={
                    'status': 'Checking voice cloning status',
                    'cloned_voice_id': cloned_voice_id,
                    'checks': checks + 1,
                    'max_checks': max_checks
                })
                
                # Wait for next check
                time.sleep(interval)
                checks += 1
            
            # If we reach here, max checks exceeded
            cloned_voice.status = 'failed'
            db.session.commit()
            
            return {
                'success': False,
                'status': 'failed',
                'cloned_voice_id': cloned_voice.id,
                'error': 'Voice cloning timed out'
            }
            
    except Exception as e:
        current_app.logger.error(f"Error in update_voice_status_task: {str(e)}")
        return {
            'success': False,
            'error': f'Voice status check error: {str(e)}'
        }
