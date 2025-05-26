"""
Video generation Celery tasks
"""
import os
import logging
from pathlib import Path
from celery import current_task
from ..extensions import celery, db
from ..models import Job, JobStep, Asset
from ..services.video import KDTalkerClient, VideoGenerationConfig
from ..services.storage import storage_service

logger = logging.getLogger(__name__)


@celery.task(bind=True)
def generate_video(self, job_id: int, portrait_asset_id: int, audio_asset_id: int):
    """
    Generate talking-head video using KDTalker
    
    Args:
        job_id: ID of the job tracking this generation
        portrait_asset_id: ID of the portrait image asset
        audio_asset_id: ID of the audio file asset
    
    Returns:
        dict: Video generation results
    """
    try:
        # Update job progress
        self.update_state(state='PROGRESS', meta={
            'progress': 5, 
            'status': 'Initializing video generation'
        })
        
        # Get job and validate
        with celery.app.app_context():
            job = Job.query.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status
            job.status = 'running'
            job.progress = 5
            job.status_message = 'Initializing video generation'
            db.session.commit()
            
            # Get assets
            portrait_asset = Asset.query.filter_by(
                id=portrait_asset_id, 
                user_id=job.user_id,
                asset_type='portrait'
            ).first()
            
            audio_asset = Asset.query.filter_by(
                id=audio_asset_id,
                user_id=job.user_id,
                asset_type='voice_sample'  # Could be TTS output or voice sample
            ).first()
            
            if not portrait_asset:
                raise ValueError(f"Portrait asset {portrait_asset_id} not found or not accessible")
            if not audio_asset:
                raise ValueError(f"Audio asset {audio_asset_id} not found or not accessible")
            
            if portrait_asset.status != 'ready':
                raise ValueError(f"Portrait asset is not ready (status: {portrait_asset.status})")
            if audio_asset.status != 'ready':
                raise ValueError(f"Audio asset is not ready (status: {audio_asset.status})")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 15, 
            'status': 'Downloading input assets'
        })
        
        # Download assets from MinIO using storage service
        # Create temp directory for processing
        temp_dir = Path(f"/tmp/video_gen_{job_id}")
        temp_dir.mkdir(exist_ok=True)
        
        # Download portrait image
        portrait_local_path = temp_dir / f"portrait_{portrait_asset.id}{Path(portrait_asset.filename).suffix}"
        storage_service.download_file(
            portrait_asset.storage_path,
            str(portrait_local_path)
        )
        
        # Download audio file
        audio_local_path = temp_dir / f"audio_{audio_asset.id}{Path(audio_asset.filename).suffix}"
        storage_service.download_file(
            audio_asset.storage_path,
            str(audio_local_path)
        )
        
        logger.info(f"Downloaded assets: portrait={portrait_local_path}, audio={audio_local_path}")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 30, 
            'status': 'Preparing KDTalker generation'
        })
        
        # Initialize KDTalker client
        kdtalker_client = KDTalkerClient()
        
        # Validate KDTalker service is available
        health_check = kdtalker_client.health_check()
        if health_check['status'] != 'healthy':
            raise ValueError(f"KDTalker service unavailable: {health_check.get('error', 'Unknown error')}")
        
        # Prepare video generation config from job parameters
        job_params = job.parameters or {}
        config = VideoGenerationConfig(
            enhancer=job_params.get('enhancer', 'gfpgan'),
            face_enhance=job_params.get('face_enhance', True),
            background_enhance=job_params.get('background_enhance', True),
            preprocess=job_params.get('preprocess', 'crop'),
            fps=job_params.get('fps', 25),
            use_blink=job_params.get('use_blink', True),
            exp_scale=job_params.get('exp_scale', 1.0)
        )
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 40, 
            'status': 'Generating video with KDTalker'
        })
        
        # Generate output path
        output_filename = f"video_{job_id}_{int(job.created_at.timestamp())}.mp4"
        output_local_path = temp_dir / output_filename
        
        # Generate video using KDTalker
        generation_result = kdtalker_client.generate_video(
            portrait_path=portrait_local_path,
            audio_path=audio_local_path,
            output_path=output_local_path,
            config=config
        )
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 80, 
            'status': 'Uploading generated video'
        })
        
        # Upload generated video to MinIO
        storage_path = f"generated/videos/{job.user_id}/{output_filename}"
        storage_service.upload_file(
            str(output_local_path),
            storage_path,
            content_type="video/mp4"
        )
        
        # Generate thumbnail
        thumbnail_path = generate_video_thumbnail_sync(str(output_local_path))
        if thumbnail_path:
            thumbnail_filename = f"thumb_{job_id}_{int(job.created_at.timestamp())}.jpg"
            thumbnail_storage_path = f"generated/thumbnails/{job.user_id}/{thumbnail_filename}"
            storage_service.upload_file(
                thumbnail_path,
                thumbnail_storage_path,
                content_type="image/jpeg"
            )
        else:
            thumbnail_storage_path = None
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 95, 
            'status': 'Finalizing video generation'
        })
        
        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp directory {temp_dir}: {e}")
        
        # Prepare final result
        video_file_size = Path(output_local_path).stat().st_size
        
        result = {
            'status': 'completed',
            'video_storage_path': storage_path,
            'thumbnail_storage_path': thumbnail_storage_path,
            'file_size': video_file_size,
            'generation_time': generation_result.get('generation_time', 0),
            'config': generation_result.get('config', {}),
            'kdtalker_result': generation_result,
            'assets_used': {
                'portrait_asset_id': portrait_asset_id,
                'audio_asset_id': audio_asset_id
            }
        }
        
        # Update job in database
        with celery.app.app_context():
            job = Job.query.get(job_id)
            job.status = 'completed'
            job.progress = 100
            job.status_message = 'Video generation completed successfully'
            job.result_data = result
            db.session.commit()
        
        logger.info(f"Video generation completed successfully: {storage_path}")
        return result
        
    except Exception as exc:
        logger.error(f"Video generation failed for job {job_id}: {exc}")
        
        # Update job status in database
        try:
            with celery.app.app_context():
                job = Job.query.get(job_id)
                if job:
                    job.status = 'failed'
                    job.status_message = str(exc)
                    job.progress = 0
                    db.session.commit()
        except Exception as db_exc:
            logger.error(f"Failed to update job status in database: {db_exc}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'progress': 0}
        )
        raise exc


def generate_video_thumbnail_sync(video_path: str, timestamp: float = 2.0) -> str:
    """
    Generate thumbnail from video using FFmpeg (synchronous version)
    
    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds to extract thumbnail
    
    Returns:
        Path to generated thumbnail or None if failed
    """
    try:
        import subprocess
        
        thumbnail_path = video_path.replace('.mp4', '_thumb.jpg')
        
        # Use FFmpeg to extract frame
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-f', 'image2',
            '-y',  # Overwrite output file
            thumbnail_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and Path(thumbnail_path).exists():
            return thumbnail_path
        else:
            logger.error(f"FFmpeg thumbnail generation failed: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None


@celery.task(bind=True)
def validate_video_service(self):
    """
    Validate KDTalker video generation service availability.
    
    Returns:
        dict: Service validation results
    """
    try:
        client = KDTalkerClient()
        
        # Perform health check
        health_check = client.health_check()
        
        result = {
            'service': 'kdtalker',
            'status': health_check['status'],
            'space': client.space_name,
            'health_check': health_check,
            'timestamp': __import__('time').time()
        }
        
        return result
        
    except Exception as exc:
        error_result = {
            'service': 'kdtalker',
            'status': 'error',
            'error': str(exc),
            'timestamp': __import__('time').time()
        }
        
        logger.error(f"KDTalker service validation failed: {exc}")
        return error_result


@celery.task(bind=True)
def generate_video_thumbnail(self, video_path, timestamp=2.0):
    """
    Generate thumbnail from video
    
    Args:
        video_path: Path to video file
        timestamp: Timestamp in seconds to extract thumbnail
    
    Returns:
        dict: Thumbnail generation results
    """
    try:
        # TODO: Implement FFmpeg thumbnail generation
        # 1. Extract frame at specified timestamp
        # 2. Resize to appropriate thumbnail size
        # 3. Save as JPEG
        
        # Placeholder implementation
        import time
        time.sleep(1)
        
        result = {
            'thumbnail_path': video_path.replace('.mp4', '_thumb.jpg'),
            'timestamp': timestamp,
            'size': '256x256',
            'status': 'completed'
        }
        
        return result
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc)}
        )
        raise exc


@celery.task(bind=True)
def full_generation_pipeline(self, portrait_asset_id, voice_asset_id, script_text, user_id):
    """
    Complete end-to-end video generation pipeline
    
    Args:
        portrait_asset_id: ID of portrait asset
        voice_asset_id: ID of voice reference asset
        script_text: Text script to convert to speech
        user_id: ID of the user requesting generation
    
    Returns:
        dict: Complete pipeline results
    """
    try:
        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 5, 'status': 'Starting full pipeline'})
        
        # TODO: Implement complete pipeline
        # 1. Clone voice from reference
        # 2. Generate TTS from script
        # 3. Convert audio format
        # 4. Generate talking-head video
        # 5. Generate thumbnail
        # 6. Store all results
        
        # Chain subtasks (placeholder)
        from .voice_tasks import clone_voice_task
        from .tts_tasks import text_to_speech_task, convert_audio_format
        
        self.update_state(state='PROGRESS', meta={'progress': 15, 'status': 'Cloning voice'})
        # voice_result = clone_voice_task.delay(voice_asset_path, user_id)
        
        self.update_state(state='PROGRESS', meta={'progress': 35, 'status': 'Generating speech'})
        # tts_result = text_to_speech_task.delay(script_text, voice_clone_id, user_id)
        
        self.update_state(state='PROGRESS', meta={'progress': 55, 'status': 'Converting audio format'})
        # audio_result = convert_audio_format.delay(tts_path, converted_path)
        
        self.update_state(state='PROGRESS', meta={'progress': 75, 'status': 'Generating video'})
        # video_result = generate_talking_head_video.delay(portrait_path, audio_path, user_id)
        
        self.update_state(state='PROGRESS', meta={'progress': 95, 'status': 'Finalizing results'})
        
        # Mock result for now
        result = {
            'video_id': 123,
            'video_path': 'generated/video/complete_123.mp4',
            'thumbnail_path': 'generated/thumbnails/complete_123.jpg',
            'audio_path': 'generated/audio/complete_123.wav',
            'duration': 45.2,
            'quality_scores': {
                'voice_similarity': 0.88,
                'lip_sync': 0.94,
                'overall': 0.91
            },
            'status': 'completed'
        }
        
        return result
        
    except Exception as exc:
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'progress': 0}
        )
        raise exc
