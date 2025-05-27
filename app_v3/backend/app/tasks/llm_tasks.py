"""
Celery tasks for LLM script generation
"""
import logging
from typing import Dict, Any, Optional
from flask import current_app

from ..extensions import db, celery
from ..models import Job, Asset
from ..models.job import JobStatus
from ..models.asset import AssetType, AssetStatus
from ..services.llm import create_llama_client, LlamaConfig
from ..services.storage import storage_service

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='generate_script')
def generate_script(self, job_id: int, prompt: str, **kwargs):
    """
    Generate a script using Llama-4 LLM service.
    
    Args:
        job_id: ID of the job to process
        prompt: Main prompt for script generation
        **kwargs: Additional parameters (topic, target_audience, duration_minutes, style, additional_context)
    
    Returns:
        Dict with generation results
    """
    job = None
    
    # Get Flask app instance for context
    from ..extensions import celery
    app = celery.flask_app
    
    with app.app_context():
        try:
            # Update task state
            self.update_state(
                state='PROGRESS',
                meta={'progress': 0, 'message': 'Initializing script generation'}
            )
            
            # Get job from database
            job = Job.query.get(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Update job status
            job.status = JobStatus.PROCESSING
            job.started_at = db.func.now()
            job.update_progress(10, "Initializing script generation")
            db.session.commit()
        
            self.update_state(
                state='PROGRESS',
                meta={'progress': 10, 'message': 'Connecting to Llama service'}
            )
            
            # Initialize Llama client
            llama_config = LlamaConfig()
            llama_client = create_llama_client(llama_config)
            
            # Update progress
            job.update_progress(20, "Connecting to Llama service")
            db.session.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={'progress': 20, 'message': 'Generating script content'}
            )
            
            # Generate script
            generation_result = llama_client.generate_script(
                prompt=prompt,
                topic=kwargs.get('topic'),
                target_audience=kwargs.get('target_audience'),
                duration_minutes=kwargs.get('duration_minutes'),
                style=kwargs.get('style'),
                additional_context=kwargs.get('additional_context')
            )
            
            if not generation_result.get('success'):
                raise RuntimeError(f"Script generation failed: {generation_result.get('error')}")
            
            # Update progress
            job.update_progress(70, "Saving generated script")
            db.session.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={'progress': 70, 'message': 'Saving generated script'}
            )
            
            # Save script as asset
            script_content = generation_result['script']
            script_filename = f"script_{job_id}.txt"
            
            # Generate storage path and get bucket name
            from ..api.assets import generate_storage_path
            storage_path = generate_storage_path(job.user_id, 'script', script_filename)
            bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
            
            # Upload script to storage
            script_asset = Asset(
                filename=f"script_{job.id}_{job.user_id}.txt",
                original_filename=script_filename,
                storage_path=storage_path,
                storage_bucket=bucket_name,
                file_size=len(script_content.encode('utf-8')),
                mime_type='text/plain',
                file_extension='.txt',
                asset_type=AssetType.SCRIPT,
                status=AssetStatus.PROCESSING,
                user_id=job.user_id,
                asset_metadata={
                    'generation_prompt': prompt,
                    'word_count': generation_result['metadata']['word_count'],
                    'estimated_duration': generation_result['metadata']['estimated_duration'],
                    'topic': kwargs.get('topic'),
                    'target_audience': kwargs.get('target_audience'),
                    'style': kwargs.get('style')
                }
            )
            
            db.session.add(script_asset)
            db.session.flush()  # Get asset ID
            
            # Save script content to storage
            try:
                from io import BytesIO
                script_file = BytesIO(script_content.encode('utf-8'))
                
                storage_result = storage_service.upload_file(
                    file_data=script_file,
                    object_name=storage_path,
                    bucket_name=bucket_name,
                    content_type='text/plain'
                )
                
                if storage_result.get('success'):
                    script_asset.status = AssetStatus.READY
                    # Generate presigned URL for download
                    script_asset.download_url = storage_service.get_presigned_url(storage_path, bucket_name)
                else:
                    script_asset.status = AssetStatus.ERROR
                
            except Exception as e:
                logger.error(f"Failed to save script to storage: {e}")
                script_asset.status = AssetStatus.ERROR
            
            # Update progress
            job.update_progress(90, "Finalizing script generation")
            db.session.commit()
            
            self.update_state(
                state='PROGRESS',
                meta={'progress': 90, 'message': 'Finalizing script generation'}
            )
            
            # Update job with results
            job.status = JobStatus.COMPLETED
            job.completed_at = db.func.now()
            job.progress_percentage = 100
            job.results = {
                'script_asset_id': script_asset.id,
                'script_content': script_content[:500] + '...' if len(script_content) > 500 else script_content,
                'metadata': generation_result['metadata'],
                'analysis': generation_result['analysis']
            }
            
            # Associate script asset with job
            job.add_asset(script_asset)
            
            db.session.commit()
            
            logger.info(f"Script generation completed successfully for job {job_id}")
            
            return {
                'success': True,
                'job_id': job_id,
                'script_asset_id': script_asset.id,
                'word_count': generation_result['metadata']['word_count'],
                'estimated_duration': generation_result['metadata']['estimated_duration']
            }
        
        except Exception as e:
            logger.error(f"Script generation failed for job {job_id}: {e}")
            
            if job:
                job.status = JobStatus.FAILED
                job.completed_at = db.func.now()
                job.error_info = {
                    'error': str(e),
                    'task_id': self.request.id,
                    'stage': 'script_generation'
                }
                db.session.commit()
            
            # Update task state to FAILURE
            self.update_state(
                state='FAILURE',
                meta={'error': str(e), 'job_id': job_id}
            )
            
            raise


@celery.task(bind=True, name='validate_llm_service')
def validate_llm_service(self):
    """
    Validate that the LLM service is accessible and functioning.
    
    Returns:
        Dict with service validation results
    """
    try:
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'message': 'Initializing LLM service validation'}
        )
        
        # Create client and test connection
        llama_config = LlamaConfig()
        llama_client = create_llama_client(llama_config)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 50, 'message': 'Testing LLM service health'}
        )
        
        # Perform health check
        health_result = llama_client.health_check()
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'message': 'LLM service validation complete'}
        )
        
        return {
            'success': True,
            'status': health_result['status'],
            'service': 'llama_4',
            'space_name': llama_config.space_name,
            'details': health_result
        }
        
    except Exception as e:
        logger.error(f"LLM service validation failed: {e}")
        
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        
        return {
            'success': False,
            'status': 'unhealthy',
            'service': 'llama_4',
            'error': str(e)
        }
