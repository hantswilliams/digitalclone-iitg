"""
Text-to-speech Celery tasks
"""
import os
import logging
import subprocess
from io import BytesIO
from celery import current_task
from flask import current_app

from ..extensions import celery, db
from ..models import Job, JobStep, Asset
from ..services.tts import ZyphraClient
from ..services.storage import storage_service

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def generate_speech(self, job_id: int, text: str, voice_asset_id: int):
    """
    Generate speech using Zyphra TTS with voice cloning.
    
    Args:
        job_id: ID of the job to update with progress
        text: Text to convert to speech
        voice_asset_id: ID of the voice asset for cloning
    
    Returns:
        dict: Speech generation results with audio file paths
    """
    job = None
    try:
        # Get job and update progress
        job = Job.query.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 5, 'status': 'Loading voice asset'})
        job.update_progress(5, 'Loading voice asset for cloning')
        
        # Get the voice asset
        voice_asset = Asset.query.get(voice_asset_id)
        if not voice_asset:
            raise ValueError(f"Voice asset {voice_asset_id} not found")
        
        if voice_asset.asset_type != 'voice_sample':
            raise ValueError(f"Asset {voice_asset_id} is not a voice sample")
        
        # Download voice asset from MinIO
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Downloading reference voice'})
        job.update_progress(10, 'Downloading reference voice from storage')
        
        voice_audio_data = storage_service.download_file(voice_asset.file_path)
        
        # Initialize Zyphra client
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Initializing TTS service'})
        job.update_progress(20, 'Connecting to Zyphra TTS service')
        
        zyphra_client = ZyphraClient()
        
        # Generate speech using Zyphra
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Generating speech with voice clone'})
        job.update_progress(30, 'Generating speech with cloned voice')
        
        speech_webm_data = zyphra_client.generate_speech(
            text=text,
            speaker_audio=voice_audio_data,
            speaking_rate=15.0  # TODO: Make this configurable
        )
        
        # Store the WebM audio in MinIO
        self.update_state(state='PROGRESS', meta={'progress': 60, 'status': 'Storing generated speech'})
        job.update_progress(60, 'Storing generated audio file')
        
        # Generate unique filename
        webm_filename = f"speech/{job_id}/generated_speech.webm"
        webm_result = storage_service.upload_file(
            file_data=speech_webm_data,
            object_name=webm_filename,
            content_type='audio/webm'
        )
        
        if not webm_result.get('success'):
            raise RuntimeError(f"Failed to upload WebM file: {webm_result.get('error')}")
        
        # Convert WebM to WAV for compatibility with video generation
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Converting audio format'})
        job.update_progress(70, 'Converting audio to WAV format')
        
        wav_data = convert_webm_to_wav(speech_webm_data)
        wav_filename = f"speech/{job_id}/generated_speech.wav"
        wav_result = storage_service.upload_file(
            file_data=wav_data,
            object_name=wav_filename,
            content_type='audio/wav'
        )
        
        if not wav_result.get('success'):
            raise RuntimeError(f"Failed to upload WAV file: {wav_result.get('error')}")
        
        # Calculate audio metadata
        self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing results'})
        job.update_progress(90, 'Processing audio metadata')
        
        # Create result data
        result = {
            'webm_file_path': webm_filename,
            'webm_storage_result': webm_result,
            'wav_file_path': wav_filename,
            'wav_storage_result': wav_result,
            'text_length': len(text),
            'voice_asset_id': voice_asset_id,
            'duration_estimated': len(text) * 0.05,  # Rough estimate: 50ms per character
            'status': 'completed'
        }
        
        # Update job with final progress
        job.update_progress(100, 'Speech generation completed successfully')
        
        logger.info(f"Successfully generated speech for job {job_id}: {len(speech_webm_data)} bytes WebM, {len(wav_data)} bytes WAV")
        return result
        
    except Exception as exc:
        error_msg = f"Speech generation failed: {str(exc)}"
        logger.error(f"Job {job_id} - {error_msg}")
        
        if job:
            job.update_progress(0, error_msg)
            job.status = 'failed'
            job.error_message = error_msg
            db.session.commit()
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg, 'progress': 0}
        )
        raise exc


def convert_webm_to_wav(webm_data: bytes) -> bytes:
    """
    Convert WebM audio data to WAV format using FFmpeg.
    
    Args:
        webm_data: WebM audio data as bytes
        
    Returns:
        WAV audio data as bytes
        
    Raises:
        RuntimeError: If conversion fails
    """
    try:
        # Use FFmpeg to convert WebM to WAV
        # Input from stdin, output to stdout
        cmd = [
            'ffmpeg',
            '-i', 'pipe:0',  # Read from stdin
            '-f', 'wav',     # Output format
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',  # 16kHz sample rate (good for KDTalker)
            '-ac', '1',      # Mono channel
            '-y',            # Overwrite output
            'pipe:1'         # Write to stdout
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        wav_data, stderr = process.communicate(input=webm_data)
        
        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg conversion failed: {stderr.decode()}")
        
        logger.debug(f"Converted {len(webm_data)} bytes WebM to {len(wav_data)} bytes WAV")
        return wav_data
        
    except FileNotFoundError:
        raise RuntimeError("FFmpeg not found. Please install FFmpeg for audio conversion.")
    except Exception as e:
        raise RuntimeError(f"Audio conversion failed: {str(e)}")


@celery.task(bind=True)  
def text_to_speech_task(self, text, voice_clone_id, user_id):
    """
    Legacy task - redirects to generate_speech task.
    
    Args:
        text: Text to convert to speech
        voice_clone_id: ID of the cloned voice to use  
        user_id: ID of the user requesting TTS
    
    Returns:
        dict: TTS generation results
    """
    # Create a temporary job for legacy compatibility
    job = Job(
        user_id=user_id,
        job_type='text_to_speech',
        status='pending',
        parameters={'text': text, 'voice_asset_id': voice_clone_id}
    )
    db.session.add(job)
    db.session.commit()
    
    # Call the new generate_speech task
    return generate_speech.apply_async(args=[job.id, text, voice_clone_id]).get()


@celery.task(bind=True)
def convert_audio_format(self, input_path: str, output_path: str, target_format: str = 'wav'):
    """
    Convert audio file format using FFmpeg.
    
    Args:
        input_path: Path to input audio file in MinIO
        output_path: Path for output audio file in MinIO
        target_format: Target audio format (wav, mp3, etc.)
    
    Returns:
        dict: Conversion results
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Downloading source audio'})
        
        # Download source file from MinIO
        source_data = storage_service.download_file(input_path)
        
        self.update_state(state='PROGRESS', meta={'progress': 30, 'status': f'Converting to {target_format}'})
        
        # Determine FFmpeg parameters based on target format
        if target_format == 'wav':
            cmd = [
                'ffmpeg', '-i', 'pipe:0',
                '-f', 'wav', '-acodec', 'pcm_s16le',
                '-ar', '16000', '-ac', '1',
                '-y', 'pipe:1'
            ]
            content_type = 'audio/wav'
        elif target_format == 'mp3':
            cmd = [
                'ffmpeg', '-i', 'pipe:0',
                '-f', 'mp3', '-acodec', 'libmp3lame',
                '-ar', '22050', '-ab', '128k',
                '-y', 'pipe:1'
            ]
            content_type = 'audio/mpeg'
        else:
            raise ValueError(f"Unsupported target format: {target_format}")
        
        # Execute conversion
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        converted_data, stderr = process.communicate(input=source_data)
        
        if process.returncode != 0:
            raise RuntimeError(f"Audio conversion failed: {stderr.decode()}")
        
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Uploading converted audio'})
        
        # Upload converted file to MinIO
        upload_result = storage_service.upload_file(
            file_data=converted_data,
            object_name=output_path,
            content_type=content_type
        )
        
        if not upload_result.get('success'):
            raise RuntimeError(f"Failed to upload converted file: {upload_result.get('error')}")
        
        result = {
            'input_path': input_path,
            'output_path': output_path,
            'upload_result': upload_result,
            'format': target_format,
            'size_bytes': len(converted_data),
            'status': 'completed'
        }
        
        logger.info(f"Converted audio {input_path} to {output_path} ({target_format})")
        return result
        
    except Exception as exc:
        error_msg = f"Audio conversion failed: {str(exc)}"
        logger.error(error_msg)
        
        self.update_state(
            state='FAILURE',
            meta={'error': error_msg}
        )
        raise exc


@celery.task(bind=True)
def validate_tts_service(self):
    """
    Validate that the TTS service (Zyphra) is accessible and working.
    
    Returns:
        dict: Validation results
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Checking Zyphra configuration'})
        
        # Initialize client and check configuration
        zyphra_client = ZyphraClient()
        config_result = zyphra_client.validate_configuration()
        
        if not config_result['valid']:
            return {
                'status': 'failed',
                'error': 'Invalid configuration',
                'issues': config_result['issues']
            }
        
        self.update_state(state='PROGRESS', meta={'progress': 60, 'status': 'Testing API connectivity'})
        
        # Test API connectivity
        health_result = zyphra_client.health_check()
        
        result = {
            'status': 'success' if health_result['status'] == 'healthy' else 'failed',
            'api_status': health_result['status'],
            'api_url': health_result['api_url'],
            'configuration': config_result,
            'health_check': health_result
        }
        
        logger.info(f"TTS service validation: {result['status']}")
        return result
        
    except Exception as exc:
        error_msg = f"TTS service validation failed: {str(exc)}"
        logger.error(error_msg)
        
        self.update_state(
            state='FAILURE', 
            meta={'error': error_msg}
        )
        raise exc
