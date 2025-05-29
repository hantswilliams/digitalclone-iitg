"""
Video generation Celery tasks
"""
import os
import logging
from pathlib import Path
from celery import current_task
from ..extensions import celery, db
from ..models import Job, JobStep, Asset, JobStatus
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
        logger.info(f"🎬 ================== VIDEO GENERATION STARTED ==================")
        logger.info(f"🆔 Job ID: {job_id}")
        logger.info(f"🖼️ Portrait Asset ID: {portrait_asset_id}")
        logger.info(f"🎵 Audio Asset ID: {audio_asset_id}")
        logger.info(f"⏰ Task started at: {current_task.request.id}")
        
        # Update job progress
        self.update_state(state='PROGRESS', meta={
            'progress': 5, 
            'status': 'Initializing video generation'
        })
        logger.info(f"📊 Updated job progress to 5%")
        
        # Get job and validate
        with celery.flask_app.app_context():
            logger.info(f"🔍 Loading job from database...")
            job = Job.query.get(job_id)
            if not job:
                logger.error(f"❌ Job {job_id} not found")
                raise ValueError(f"Job {job_id} not found")
            
            logger.info(f"✅ Job loaded: {job.title} (type: {job.job_type})")
            logger.info(f"📋 Job parameters: {job.parameters}")
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.progress = 5
            job.status_message = 'Initializing video generation'
            db.session.commit()
            logger.info(f"💾 Job status updated to PROCESSING")
            
            # Get assets
            from ..models.asset import AssetType, AssetStatus
            
            logger.info(f"🔍 Loading portrait asset {portrait_asset_id}...")
            portrait_asset = Asset.query.filter_by(
                id=portrait_asset_id, 
                user_id=job.user_id,
                asset_type=AssetType.PORTRAIT
            ).first()
            
            logger.info(f"🔍 Loading audio asset {audio_asset_id}...")
            audio_asset = Asset.query.filter_by(
                id=audio_asset_id,
                user_id=job.user_id,
                asset_type=AssetType.VOICE_SAMPLE  # Could be TTS output or voice sample
            ).first()
            
            # Asset validation with detailed logging
            if not portrait_asset:
                logger.error(f"❌ Portrait asset {portrait_asset_id} not found or not accessible")
                raise ValueError(f"Portrait asset {portrait_asset_id} not found or not accessible")
            if not audio_asset:
                logger.error(f"❌ Audio asset {audio_asset_id} not found or not accessible")
                raise ValueError(f"Audio asset {audio_asset_id} not found or not accessible")
            
            logger.info(f"✅ Portrait Asset: {portrait_asset.name} (status: {portrait_asset.status})")
            logger.info(f"✅ Audio Asset: {audio_asset.name} (status: {audio_asset.status})")
            
            if portrait_asset.status != AssetStatus.READY:
                logger.error(f"❌ Portrait asset is not ready (status: {portrait_asset.status})")
                raise ValueError(f"Portrait asset is not ready (status: {portrait_asset.status})")
            if audio_asset.status != AssetStatus.READY:
                logger.error(f"❌ Audio asset is not ready (status: {audio_asset.status})")
                raise ValueError(f"Audio asset is not ready (status: {audio_asset.status})")
        
            # Update progress
            self.update_state(state='PROGRESS', meta={
                'progress': 15, 
                'status': 'Downloading input assets'
            })
            logger.info(f"📊 Updated job progress to 15% - Downloading assets")
            
            # Download assets from MinIO using storage service
            # Create temp directory for processing
            temp_dir = Path(f"/tmp/video_gen_{job_id}")
            temp_dir.mkdir(exist_ok=True)
            logger.info(f"📁 Created temp directory: {temp_dir}")
            
            # Download portrait image
            portrait_local_path = temp_dir / f"portrait_{portrait_asset.id}{Path(portrait_asset.filename).suffix}"
            logger.info(f"⬇️ Downloading portrait from: {portrait_asset.storage_path}")
            portrait_data = storage_service.download_file(portrait_asset.storage_path)
            if not portrait_data:
                logger.error(f"❌ Failed to download portrait asset from storage: {portrait_asset.storage_path}")
                raise ValueError(f"Failed to download portrait asset from storage: {portrait_asset.storage_path}")
            
            with open(portrait_local_path, 'wb') as f:
                f.write(portrait_data)
            logger.info(f"✅ Portrait downloaded to: {portrait_local_path} ({len(portrait_data)} bytes)")
            
            # Download audio file
            audio_local_path = temp_dir / f"audio_{audio_asset.id}{Path(audio_asset.filename).suffix}"
            logger.info(f"⬇️ Downloading audio from: {audio_asset.storage_path}")
            audio_data = storage_service.download_file(audio_asset.storage_path)
            if not audio_data:
                logger.error(f"❌ Failed to download audio asset from storage: {audio_asset.storage_path}")
                raise ValueError(f"Failed to download audio asset from storage: {audio_asset.storage_path}")
            
            with open(audio_local_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"✅ Audio downloaded to: {audio_local_path} ({len(audio_data)} bytes)")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 30, 
            'status': 'Preparing KDTalker generation'
        })
        logger.info(f"📊 Updated job progress to 30% - Preparing KDTalker generation")
        
        # Initialize KDTalker client
        kdtalker_client = KDTalkerClient()
        
        # Validate KDTalker service is available
        logger.info(f"🛠️ Initializing KDTalker client...")
        health_check = kdtalker_client.health_check()
        if health_check['status'] != 'healthy':
            logger.error(f"❌ KDTalker service unavailable: {health_check.get('error', 'Unknown error')}")
            raise ValueError(f"KDTalker service unavailable: {health_check.get('error', 'Unknown error')}")
        logger.info(f"✅ KDTalker service is healthy")
        
        # Prepare video generation config from job parameters
        job_params = job.parameters or {}
        config = VideoGenerationConfig(
            driven_audio_type=job_params.get('driven_audio_type', 'upload'),
            smoothed_pitch=job_params.get('smoothed_pitch', 0.8),
            smoothed_yaw=job_params.get('smoothed_yaw', 0.8),
            smoothed_roll=job_params.get('smoothed_roll', 0.8),
            smoothed_t=job_params.get('smoothed_t', 0.8)
        )
        logger.info(f"⚙️ Video generation config: {config.__dict__}")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 40, 
            'status': 'Generating video with KDTalker'
        })
        logger.info(f"📊 Updated job progress to 40% - Generating video")
        
        # Generate output path
        output_filename = f"video_{job_id}_{int(job.created_at.timestamp())}.mp4"
        output_local_path = temp_dir / output_filename
        logger.info(f"📄 Output file will be: {output_local_path}")
        
        logger.info(f"🎥 Starting KDTalker video generation...")
        logger.info(f"  - Portrait: {portrait_local_path}")
        logger.info(f"  - Audio: {audio_local_path}")
        logger.info(f"  - Output: {output_local_path}")
        
        # Generate video using KDTalker
        import time
        generation_start_time = time.time()
        logger.info(f"⏱️ Generation started at: {generation_start_time}")
        generation_result = kdtalker_client.generate_video(
            portrait_path=portrait_local_path,
            audio_path=audio_local_path,
            output_path=output_local_path,
            config=config
        )
        generation_end_time = time.time()
        generation_duration = generation_end_time - generation_start_time
        
        logger.info(f"✅ Video generation completed in {generation_duration:.2f} seconds")
        logger.info(f"📊 Generation result: {generation_result}")
        
        # Check if output file was created
        if not output_local_path.exists():
            logger.error(f"❌ Output video file not created: {output_local_path}")
            raise ValueError(f"Video generation failed - output file not created")
        
        video_size = output_local_path.stat().st_size
        logger.info(f"✅ Output video created: {video_size} bytes ({video_size / 1024 / 1024:.2f} MB)")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 80, 
            'status': 'Uploading generated video'
        })
        logger.info(f"📊 Updated job progress to 80% - Uploading video")
        
        # Upload generated video to MinIO and create database records
        with celery.flask_app.app_context():
            storage_path = f"generated/videos/{job.user_id}/{output_filename}"
            logger.info(f"📤 Uploading video to storage: {storage_path}")
            
            # Upload video file
            upload_start_time = time.time()
            with open(output_local_path, 'rb') as video_file:
                upload_result = storage_service.upload_file(
                    file_data=video_file,
                    object_name=storage_path,
                    content_type="video/mp4"
                )
            logger.info(f"✅ Video uploaded to storage")
            
            # Generate thumbnail
            logger.info(f"🖼️ Generating thumbnail for video...")
            thumbnail_path = generate_video_thumbnail_sync(str(output_local_path))
            if thumbnail_path:
                thumbnail_filename = f"thumb_{job_id}_{int(job.created_at.timestamp())}.jpg"
                thumbnail_storage_path = f"generated/thumbnails/{job.user_id}/{thumbnail_filename}"
                
                logger.info(f"📤 Uploading thumbnail to storage: {thumbnail_storage_path}")
                # Upload thumbnail file
                with open(thumbnail_path, 'rb') as thumb_file:
                    storage_service.upload_file(
                        file_data=thumb_file,
                        object_name=thumbnail_storage_path,
                        content_type="image/jpeg"
                    )
                logger.info(f"✅ Thumbnail uploaded to storage")
            else:
                logger.warning(f"⚠️ Thumbnail generation failed, skipping thumbnail upload")
                thumbnail_storage_path = None
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 95, 
            'status': 'Finalizing video generation'
        })
        logger.info(f"📊 Updated job progress to 95% - Finalizing")
        
        # Get file size before cleaning up temp files
        video_file_size = Path(output_local_path).stat().st_size
        logger.info(f"📏 Video file size: {video_file_size} bytes")
        
        # Clean up temp files
        try:
            import shutil
            logger.info(f"🧹 Cleaning up temp directory {temp_dir}...")
            shutil.rmtree(temp_dir)
            logger.info(f"✅ Temp directory cleaned up")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up temp directory {temp_dir}: {e}")
        
        # Update progress
        self.update_state(state='PROGRESS', meta={
            'progress': 90, 
            'status': 'Creating asset record'
        })
        logger.info(f"📊 Updated job progress to 90% - Creating asset record")
        
        # Create Asset record for the generated video
        with celery.flask_app.app_context():
            from ..models.asset import AssetStatus, AssetType
            
            logger.info(f"Creating Asset record for video job {job_id}, user {job.user_id}")
            
            asset = Asset(
                filename=output_filename,
                original_filename=output_filename,
                file_size=video_file_size,
                mime_type='video/mp4',
                file_extension='.mp4',
                asset_type=AssetType.GENERATED_VIDEO,
                status=AssetStatus.READY,
                storage_path=storage_path,
                storage_bucket=celery.flask_app.config.get('MINIO_BUCKET_NAME', 'voice-clone-assets'),
                user_id=job.user_id,
                description=f"Generated video from portrait (asset {portrait_asset_id}) and audio (asset {audio_asset_id})"
            )
            
            db.session.add(asset)
            db.session.commit()
            
            logger.info(f"✅ Successfully created Asset record with ID {asset.id} for video output")
        
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
            },
            'generated_asset_id': asset.id  # Include the asset ID in the result
        }
        
        # Update job in database
        with celery.flask_app.app_context():
            job = Job.query.get(job_id)
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.status_message = 'Video generation completed successfully'
            job.result_data = result
            db.session.commit()
        
        logger.info(f"🎉 Video generation completed successfully: {storage_path}")
        return result
        
    except Exception as exc:
        logger.error(f"❌ Video generation failed for job {job_id}: {exc}")
        
        # Update job status in database
        try:
            with celery.flask_app.app_context():
                job = Job.query.get(job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.status_message = str(exc)
                    job.progress = 0
                    db.session.commit()
                    logger.info(f"📉 Job status updated to FAILED")
        except Exception as db_exc:
            logger.error(f"❌ Failed to update job status in database: {db_exc}")
        
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
def full_generation_pipeline(self, job_id: int, portrait_asset_id, voice_asset_id, script_text, user_id):
    """
    Complete end-to-end video generation pipeline:
    1. Generate TTS audio from script using voice clone
    2. Generate talking-head video from portrait and generated audio
    
    Args:
        job_id: ID of the main job to update with progress
        portrait_asset_id: ID of portrait asset
        voice_asset_id: ID of voice reference asset
        script_text: Text script to convert to speech
        user_id: ID of the user requesting generation
    
    Returns:
        dict: Complete pipeline results
    """
    try:
        logger.info(f"🎬 ================== FULL PIPELINE STARTED ==================")
        logger.info(f"🆔 Job ID: {job_id}")
        logger.info(f"👤 User ID: {user_id}")
        logger.info(f"🖼️ Portrait Asset ID: {portrait_asset_id}")
        logger.info(f"🎵 Voice Asset ID: {voice_asset_id}")
        logger.info(f"📝 Script length: {len(script_text)} characters")
        logger.info(f"📝 Script preview: {script_text[:200] + '...' if len(script_text) > 200 else script_text}")
        
        # Update task progress
        self.update_state(state='PROGRESS', meta={'progress': 5, 'status': 'Starting full pipeline'})
        
        with celery.flask_app.app_context():
            # Import models at the beginning
            from ..tasks.tts_tasks import generate_speech
            from ..models import Job, JobStatus, JobType, JobPriority, Asset, AssetType
            
            # Get the main job and update its status
            main_job = Job.query.get(job_id)
            if not main_job:
                raise ValueError(f"Main job {job_id} not found")
            
            main_job.status = JobStatus.PROCESSING
            main_job.progress = 5
            main_job.status_message = 'Starting full pipeline'
            db.session.commit()
            logger.info(f"✅ Updated main job {job_id} status to PROCESSING")
            
            # Step 1: Generate TTS audio from script using voice clone
            logger.info("🗣️ Step 1: Generating TTS audio from script...")
            self.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Generating speech from script'})
            main_job.update_progress(10, 'Generating speech from script')
            
            # Create a sub-job for TTS generation
            tts_job = Job(
                title=f"TTS for Full Pipeline",
                description=f"Generate speech for full pipeline",
                job_type=JobType.TEXT_TO_SPEECH,
                priority=JobPriority.HIGH,
                user_id=user_id,
                parameters={
                    'text': script_text,
                    'voice_asset_id': voice_asset_id,
                    'parent_pipeline': True
                },
                estimated_duration=len(script_text) * 0.1
            )
            
            db.session.add(tts_job)
            db.session.commit()
            logger.info(f"✅ Created TTS sub-job: {tts_job.id}")
            
            # Generate speech synchronously (blocking)
            logger.info("🎤 Generating speech...")
            tts_result = generate_speech.apply(
                args=[tts_job.id, script_text, voice_asset_id]
            )
            
            if tts_result.failed():
                logger.error(f"❌ TTS generation failed: {tts_result.result}")
                raise ValueError(f"TTS generation failed: {tts_result.result}")
            
            tts_data = tts_result.result
            generated_audio_asset_id = tts_data.get('generated_asset_id')
            
            if not generated_audio_asset_id:
                logger.error("❌ TTS did not return generated_asset_id")
                raise ValueError("TTS generation did not produce audio asset ID")
            
            logger.info(f"✅ TTS completed. Generated audio asset ID: {generated_audio_asset_id}")
            
            # Verify the audio asset exists before proceeding
            logger.info(f"🔍 Verifying audio asset {generated_audio_asset_id} exists...")
            audio_asset = Asset.query.get(generated_audio_asset_id)
            if not audio_asset:
                logger.error(f"❌ Audio asset {generated_audio_asset_id} not found in database after TTS!")
                # Try to refresh the session
                db.session.expire_all()
                audio_asset = Asset.query.get(generated_audio_asset_id)
                if not audio_asset:
                    raise ValueError(f"Audio asset {generated_audio_asset_id} not found even after session refresh")
            
            logger.info(f"✅ Audio asset verified: {audio_asset.id} - {audio_asset.original_filename} ({audio_asset.status})")
            
            # Small delay to ensure database consistency
            import time
            time.sleep(1)
            logger.info("⏳ Database sync delay completed")
            
            # Verify the generated audio asset exists and is accessible
            logger.info("🔍 Verifying generated audio asset exists...")
            generated_audio_asset = Asset.query.get(generated_audio_asset_id)
            if not generated_audio_asset:
                logger.error(f"❌ Generated audio asset {generated_audio_asset_id} not found in database!")
                logger.info("🔍 Checking all assets for this user...")
                user_assets = Asset.query.filter_by(user_id=user_id).all()
                for asset in user_assets:
                    logger.info(f"  - Asset {asset.id}: {asset.asset_type.value} - {asset.status.value}")
                raise ValueError(f"Generated audio asset {generated_audio_asset_id} was not found")
            else:
                logger.info(f"✅ Generated audio asset {generated_audio_asset_id} found: {generated_audio_asset.asset_type.value} - {generated_audio_asset.status.value}")
                logger.info(f"📁 Asset details: {generated_audio_asset.filename} ({generated_audio_asset.file_size} bytes)")
            
            # Step 2: Generate talking-head video using portrait and generated audio
            logger.info("🎥 Step 2: Generating talking-head video...")
            self.update_state(state='PROGRESS', meta={'progress': 50, 'status': 'Generating talking-head video'})
            
            # Create a sub-job for video generation
            video_job = Job(
                title=f"Video for Full Pipeline",
                description=f"Generate video for full pipeline",
                job_type=JobType.VIDEO_GENERATION,
                priority=JobPriority.HIGH,
                user_id=user_id,
                parameters={
                    'portrait_asset_id': portrait_asset_id,
                    'audio_asset_id': generated_audio_asset_id,
                    'parent_pipeline': True,
                    'driven_audio_type': 'upload',
                    'smoothed_pitch': 0.8,
                    'smoothed_yaw': 0.8,
                    'smoothed_roll': 0.8,
                    'smoothed_t': 0.8
                },
                estimated_duration=60
            )
            
            db.session.add(video_job)
            db.session.commit()
            logger.info(f"✅ Created video sub-job: {video_job.id}")
            
            # Generate video directly in this task (no separate Celery task to avoid session isolation)
            logger.info("🎬 Generating video directly in pipeline...")
            
            # Update video job status to processing
            video_job.status = JobStatus.PROCESSING
            db.session.commit()
            logger.info("💾 Video job status updated to PROCESSING")
            
            # Load portrait asset
            logger.info(f"🔍 Loading portrait asset {portrait_asset_id}...")
            portrait_asset = Asset.query.filter_by(id=portrait_asset_id, user_id=user_id).first()
            if not portrait_asset:
                raise ValueError(f"Portrait asset {portrait_asset_id} not found or not accessible")
            
            logger.info(f"✅ Portrait asset loaded: {portrait_asset.original_filename}")
            
            # Load audio asset (should be available in the same session now)
            logger.info(f"🔍 Loading audio asset {generated_audio_asset_id}...")
            audio_asset = Asset.query.filter_by(id=generated_audio_asset_id, user_id=user_id).first()
            if not audio_asset:
                # Try to refresh the session and query again
                db.session.expire_all()
                audio_asset = Asset.query.filter_by(id=generated_audio_asset_id, user_id=user_id).first()
                if not audio_asset:
                    raise ValueError(f"Audio asset {generated_audio_asset_id} not found or not accessible")
            
            logger.info(f"✅ Audio asset loaded: {audio_asset.original_filename}")
            
            # Download portrait image
            logger.info("📥 Downloading portrait image...")
            import requests
            import tempfile
            import os
            
            # Get presigned URL for portrait asset
            portrait_url = storage_service.get_presigned_url(
                object_name=portrait_asset.storage_path,
                bucket_name=portrait_asset.storage_bucket
            )
            if not portrait_url:
                raise ValueError(f"Failed to get presigned URL for portrait asset {portrait_asset_id}")
            
            portrait_response = requests.get(portrait_url)
            if portrait_response.status_code != 200:
                raise ValueError(f"Failed to download portrait image: {portrait_response.status_code}")
            
            portrait_filename = f"portrait_{portrait_asset_id}_{portrait_asset.original_filename}"
            portrait_path = os.path.join(tempfile.gettempdir(), portrait_filename)
            
            with open(portrait_path, 'wb') as f:
                f.write(portrait_response.content)
            
            logger.info(f"✅ Portrait downloaded to: {portrait_path}")
            
            # Download audio file
            logger.info("📥 Downloading audio file...")
            
            # Get presigned URL for audio asset
            audio_url = storage_service.get_presigned_url(
                object_name=audio_asset.storage_path,
                bucket_name=audio_asset.storage_bucket
            )
            if not audio_url:
                raise ValueError(f"Failed to get presigned URL for audio asset {generated_audio_asset_id}")
            
            audio_response = requests.get(audio_url)
            if audio_response.status_code != 200:
                raise ValueError(f"Failed to download audio file: {audio_response.status_code}")
            
            audio_filename = f"audio_{generated_audio_asset_id}_{audio_asset.original_filename}"
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            
            with open(audio_path, 'wb') as f:
                f.write(audio_response.content)
            
            logger.info(f"✅ Audio downloaded to: {audio_path}")
            
            # Generate video using KDTalker
            logger.info("🎬 Starting KDTalker video generation...")
            import time
            start_time = time.time()
            
            from ..services.video.kdtalker_client import KDTalkerClient, VideoGenerationConfig
            
            # Create configuration with the correct parameters
            config = VideoGenerationConfig(
                driven_audio_type="upload",
                smoothed_pitch=0.8,
                smoothed_yaw=0.8,
                smoothed_roll=0.8,
                smoothed_t=0.8
            )
            
            kdtalker_client = KDTalkerClient()
            result = kdtalker_client.generate_video(
                portrait_path=portrait_path,
                audio_path=audio_path,
                config=config
            )
            
            generation_time = time.time() - start_time
            logger.info(f"✅ KDTalker generation completed in {generation_time:.2f}s")
            
            # Get the output path from the result
            if not result or 'video_path' not in result:
                logger.error(f"❌ KDTalker result: {result}")
                raise ValueError("KDTalker did not return a valid result with video_path")
            
            output_path = result['video_path']
            logger.info(f"📁 Video generated at: {output_path}")
            
            # Verify output file exists and get size
            if not os.path.exists(output_path):
                raise ValueError(f"Generated video file not found at {output_path}")
            
            file_size = os.path.getsize(output_path)
            logger.info(f"📊 Generated video size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
            
            # Upload to storage
            logger.info("☁️ Uploading video to storage...")
            upload_start = time.time()
            
            # Read video file as bytes
            with open(output_path, 'rb') as video_file:
                video_data_bytes = video_file.read()
            
            # Generate filename for video asset
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            video_filename = f"generated_video_{video_job.id}_{timestamp}.mp4"
            storage_path = f"generated/videos/{user_id}/{video_filename}"
            
            # Upload to storage using file-like object
            import io
            video_file_obj = io.BytesIO(video_data_bytes)
            upload_result = storage_service.upload_file(
                file_data=video_file_obj,
                object_name=storage_path,
                content_type='video/mp4'
            )
            
            if not upload_result.get('success'):
                raise ValueError(f"Failed to upload video: {upload_result.get('error')}")
            
            upload_time = time.time() - upload_start
            logger.info(f"✅ Video uploaded in {upload_time:.2f}s to: {storage_path}")
            
            # Create video asset record
            logger.info("💾 Creating video asset record...")
            from flask import current_app
            from ..models import AssetStatus
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
            video_asset = Asset(
                filename=video_filename,
                original_filename=video_filename,
                asset_type=AssetType.GENERATED_VIDEO,
                storage_path=storage_path,
                storage_bucket=bucket_name,
                user_id=user_id,
                file_size=file_size,
                mime_type='video/mp4',
                file_extension='.mp4',
                status=AssetStatus.READY
            )
            
            db.session.add(video_asset)
            db.session.commit()
            
            logger.info(f"✅ Video asset created with ID: {video_asset.id}")
            
            # Update video job with result
            video_job.result_asset_id = video_asset.id
            video_job.status = JobStatus.COMPLETED
            db.session.commit()
            
            logger.info("💾 Video job status updated to COMPLETED")
            
            # Clean up temporary files
            try:
                os.unlink(portrait_path)
                os.unlink(audio_path)
                os.unlink(output_path)
                logger.info("🧹 Temporary files cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup warning: {cleanup_error}")
            
            generated_video_asset_id = video_asset.id
            logger.info(f"✅ Video generation completed. Generated video asset ID: {generated_video_asset_id}")
            
            # Create video generation data for result
            video_data = {
                'video_asset_id': generated_video_asset_id,
                'generation_time': generation_time,
                'video_duration': 'calculated_from_audio'  # Could be calculated from audio duration
            }
            
            # Step 3: Finalize pipeline
            self.update_state(state='PROGRESS', meta={'progress': 95, 'status': 'Finalizing pipeline'})
            
            # Update main job status to completed
            main_job.status = JobStatus.COMPLETED
            main_job.progress = 100
            main_job.status_message = 'Full pipeline completed successfully'
            main_job.result_asset_id = generated_video_asset_id
            db.session.commit()
            
            # Create comprehensive result
            result = {
                'status': 'completed',
                'pipeline_type': 'full_generation',
                'input': {
                    'portrait_asset_id': portrait_asset_id,
                    'voice_asset_id': voice_asset_id,
                    'script_length': len(script_text),
                    'script_preview': script_text[:100] + '...' if len(script_text) > 100 else script_text
                },
                'intermediate': {
                    'tts_job_id': tts_job.id,
                    'audio_asset_id': generated_audio_asset_id,
                    'audio_generation_time': tts_data.get('generation_time', 'unknown')
                },
                'output': {
                    'video_job_id': video_job.id,
                    'video_asset_id': generated_video_asset_id,
                    'video_generation_time': video_data.get('generation_time', 'unknown'),
                    'total_duration': video_data.get('video_duration', 'unknown')
                },
                'quality_metrics': {
                    'voice_similarity': 'estimated_high',  # Could be calculated
                    'lip_sync_quality': 'estimated_high',  # Could be calculated
                    'overall_rating': 'generated_successfully'
                }
            }
            
            logger.info(f"🎉 Full pipeline completed successfully!")
            logger.info(f"📊 Final result: {result}")
            logger.info(f"🎬 ================== FULL PIPELINE COMPLETED ==================")
            
            return result
        
    except Exception as exc:
        logger.error(f"❌ ================== FULL PIPELINE FAILED ==================")
        logger.error(f"❌ Error in full generation pipeline: {str(exc)}")
        logger.error(f"📊 Error details: {type(exc).__name__}: {str(exc)}")
        import traceback
        logger.error(f"🔍 Traceback: {traceback.format_exc()}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(exc), 'progress': 0, 'pipeline_stage': 'failed'}
        )
        logger.error(f"🎬 ================== END PIPELINE ERROR LOG ==================")
        raise exc
