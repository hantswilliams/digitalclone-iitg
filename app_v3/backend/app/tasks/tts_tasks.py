"""
Text-to-speech Celery tasks
"""
import os
import time
import logging
import subprocess
from io import BytesIO
from celery import current_task
from flask import current_app

from ..extensions import celery, db
from ..models import Job, JobStep, Asset, JobStatus, JobType
from ..models.asset import AssetType
from ..services.tts import IndexTTSClient
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
    
    # Get Flask app instance for context
    from ..extensions import celery
    app = celery.flask_app
    
    with app.app_context():
        try:
            # Get job and update progress
            job = Job.query.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status to processing when task starts with timing
            job.mark_started()
            db.session.commit()
            
            logger.info(f"Started TTS generation for job {job_id}, updated status to PROCESSING with timing")
            
            # Update task progress
            self.update_state(state='PROGRESS', meta={'progress': 5, 'status': 'Loading voice asset'})
            job.update_progress(5, 'Loading voice asset for cloning')
            
            # Get the voice asset
            voice_asset = Asset.query.get(voice_asset_id)
            if not voice_asset:
                raise ValueError(f"Voice asset {voice_asset_id} not found")
            
            if voice_asset.asset_type != AssetType.VOICE_SAMPLE:
                raise ValueError(f"Asset {voice_asset_id} is not a voice sample")
            
            # Download voice asset from MinIO
            self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Downloading reference voice'})
            job.update_progress(10, 'Downloading reference voice from storage')
            
            voice_audio_data = storage_service.download_file(voice_asset.storage_path)
            
            # Initialize IndexTTS client
            self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Initializing TTS service'})
            job.update_progress(20, 'Connecting to IndexTTS service')
            
            indextts_client = IndexTTSClient()
            
            # Generate speech using IndexTTS
            self.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Generating speech with voice clone'})
            job.update_progress(30, 'Generating speech with cloned voice')
            
            speech_audio_data = indextts_client.generate_speech(
                text=text,
                speaker_audio=voice_audio_data
            )
            
            # Capture IndexTTS metadata including hardware information
            logger.info(f"📋 Capturing IndexTTS service metadata...")
            try:
                indextts_metadata = indextts_client.get_space_metadata()
                logger.info(f"✅ IndexTTS metadata captured: {indextts_metadata.get('model_name', 'Unknown')}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to capture IndexTTS metadata: {str(e)}")
                indextts_metadata = {
                    "error": str(e),
                    "captured_at": time.time()
                }
            
            # Store the generated audio in MinIO
            self.update_state(state='PROGRESS', meta={'progress': 60, 'status': 'Storing generated speech'})
            job.update_progress(60, 'Storing generated audio file')
            
            # Generate unique filename
            audio_filename = f"speech/{job_id}/generated_speech.wav"
            
            # Convert bytes to BytesIO for MinIO compatibility
            audio_file_obj = BytesIO(speech_audio_data)
            
            audio_result = storage_service.upload_file(
                file_data=audio_file_obj,
                object_name=audio_filename,
                content_type='audio/wav'
            )
            
            if not audio_result.get('success'):
                raise RuntimeError(f"Failed to upload audio file: {audio_result.get('error')}")
            
            # IndexTTS typically outputs WAV format directly
            self.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Processing audio format'})
            job.update_progress(70, 'Processing audio format')
            
            # The speech_audio_data from IndexTTS is already in WAV format
            wav_data = speech_audio_data
            wav_filename = f"speech/{job_id}/generated_speech_wav.wav"
            
            # Convert bytes to BytesIO for MinIO compatibility
            wav_file_obj = BytesIO(wav_data)
            
            wav_result = storage_service.upload_file(
                file_data=wav_file_obj,
                object_name=wav_filename,
                content_type='audio/wav'
            )
            
            if not wav_result.get('success'):
                raise RuntimeError(f"Failed to upload WAV file: {wav_result.get('error')}")
            
            # Calculate audio metadata
            self.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing results'})
            job.update_progress(90, 'Creating asset record')
            
            # Create Asset record for the generated audio
            from ..models.asset import AssetStatus
            
            logger.info(f"Creating Asset record for job {job_id}, user {job.user_id}")
            
            asset = Asset(
                filename=f"generated_speech_{job_id}.wav",
                original_filename=f"generated_speech_{job_id}.wav",
                file_size=len(wav_data),
                mime_type='audio/wav',
                file_extension='.wav',
                asset_type=AssetType.GENERATED_AUDIO,
                status=AssetStatus.READY,
                storage_path=wav_filename,
                storage_bucket=current_app.config.get('MINIO_BUCKET_NAME', 'voice-clone-assets'),
                user_id=job.user_id,
                description=f"Generated speech from text: {text[:100]}{'...' if len(text) > 100 else ''}"
            )
            
            db.session.add(asset)
            db.session.commit()
            
            logger.info(f"Successfully created Asset record with ID {asset.id} for TTS output")
            
            # Create result data
            result = {
                'audio_file_path': audio_filename,
                'audio_storage_result': audio_result,
                'wav_file_path': wav_filename,
                'wav_storage_result': wav_result,
                'text_length': len(text),
                'voice_asset_id': voice_asset_id,
                'duration_estimated': len(text) * 0.05,  # Rough estimate: 50ms per character
                'status': 'completed',
                'generated_asset_id': asset.id  # Include the asset ID in the result
            }
            
            # Store service metadata
            service_metadata = {
                'indextts': indextts_metadata,
                'generation_timestamp': time.time(),
                'task_id': current_task.request.id
            }
            job.update_service_metadata(service_metadata)
            
            # Update job with final progress and mark as completed with timing
            job.update_progress(100, 'Speech generation completed successfully')
            job.mark_completed(result)
            db.session.commit()
            
            logger.info(f"Successfully generated speech for job {job_id}: {len(speech_audio_data)} bytes audio, {len(wav_data)} bytes WAV")
            return result
            
        except Exception as exc:
            error_msg = f"Speech generation failed: {str(exc)}"
            logger.error(f"Job {job_id} - {error_msg}")
            
            if job:
                # Mark as failed with timing and error info
                error_info = {
                    'error_message': error_msg,
                    'task_id': current_task.request.id,
                    'failed_at': time.time()
                }
                job.update_progress(0, error_msg)
                job.mark_failed(error_info)
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
        title=f'TTS Generation - {text[:30]}...' if len(text) > 30 else f'TTS Generation - {text}',
        job_type=JobType.TEXT_TO_SPEECH,
        user_id=user_id,
        status=JobStatus.PENDING,
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
    Validate that the TTS service (IndexTTS) is accessible and working.
    
    Returns:
        dict: Validation results
    """
    try:
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Checking IndexTTS configuration'})
        
        # Initialize client and check configuration
        indextts_client = IndexTTSClient()
        config_result = indextts_client.validate_configuration()
        
        if not config_result['valid']:
            return {
                'status': 'failed',
                'error': 'Invalid configuration',
                'issues': config_result['issues']
            }
        
        self.update_state(state='PROGRESS', meta={'progress': 60, 'status': 'Testing API connectivity'})
        
        # Test API connectivity
        health_result = indextts_client.health_check()
        
        result = {
            'status': 'success' if health_result['status'] == 'healthy' else 'failed',
            'api_status': health_result['status'],
            'api_url': f"IndexTTS Space: {indextts_client.space_name}",
            'configuration': config_result,
            'health_check': health_result
        }
        
        logger.info(f"TTS service validation: {result['status']}")
        return result
        
    except Exception as exc:
        error_msg = f"TTS service validation failed: {str(exc)}"
        logger.error(error_msg)
        
        # Return error state instead of raising exception
        return {
            'status': 'error',
            'api_status': 'error',
            'api_url': 'IndexTTS API',
            'error': error_msg,
            'exception_type': type(exc).__name__
        }
