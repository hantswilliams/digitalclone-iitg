"""
Job management API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import and_, or_, desc

from ..extensions import db
from ..models import Job, JobStep, Asset, JobStatus, JobType, JobPriority, StepStatus
from ..schemas import (
    JobCreateSchema, JobUpdateSchema, JobResponseSchema, JobListSchema,
    JobProgressUpdateSchema, JobStepCreateSchema, JobStepSchema,
    MessageResponseSchema, ErrorResponseSchema, PaginationSchema
)
from ..utils import handle_errors


def get_fresh_job(job_id, user_id):
    """Get a fresh job instance from database with latest data"""
    # Force database session refresh to get latest data from Celery workers
    db.session.expire_all()
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    if job:
        db.session.refresh(job)
    return job


jobs_bp = Blueprint('jobs', __name__)

# Initialize schemas
job_create_schema = JobCreateSchema()
job_update_schema = JobUpdateSchema()
job_response_schema = JobResponseSchema()
job_list_schema = JobListSchema()
job_progress_schema = JobProgressUpdateSchema()
job_step_create_schema = JobStepCreateSchema()
job_step_schema = JobStepSchema()
message_schema = MessageResponseSchema()
error_schema = ErrorResponseSchema()
pagination_schema = PaginationSchema()


@jobs_bp.route('/', methods=['GET'])
@jwt_required()
@handle_errors
def list_jobs():
    """List user's jobs with filtering and pagination"""
    user_id = get_jwt_identity()
    
    # Refresh session to get latest data from Celery workers
    db.session.expire_all()
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    job_type = request.args.get('job_type')
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    # Build query
    query = Job.query.filter_by(user_id=user_id)
    
    # Apply filters
    if job_type:
        try:
            job_type_enum = JobType(job_type)
            query = query.filter(Job.job_type == job_type_enum)
        except ValueError:
            return jsonify(error_schema.dump({
                'message': 'Invalid job type',
                'details': {'job_type': [f'Invalid job type: {job_type}']}
            })), 400
    
    if status:
        try:
            status_enum = JobStatus(status)
            query = query.filter(Job.status == status_enum)
        except ValueError:
            return jsonify(error_schema.dump({
                'message': 'Invalid status',
                'details': {'status': [f'Invalid status: {status}']}
            })), 400
    
    if priority:
        try:
            priority_enum = JobPriority(priority)
            query = query.filter(Job.priority == priority_enum)
        except ValueError:
            return jsonify(error_schema.dump({
                'message': 'Invalid priority',
                'details': {'priority': [f'Invalid priority: {priority}']}
            })), 400
    
    # Order by creation date (newest first)
    query = query.order_by(desc(Job.created_at))
    
    # Paginate
    pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    jobs = pagination.items
    
    # Serialize jobs
    jobs_data = []
    for job in jobs:
        job_dict = job.to_dict(include_details=False)
        jobs_data.append(job_dict)
    
    response_data = {
        'jobs': jobs_data,
        'pagination': {
            'page': pagination.page,
            'pages': pagination.pages,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }
    
    return jsonify(response_data), 200


@jobs_bp.route('/', methods=['POST'])
@jwt_required()
@handle_errors
def create_job():
    """Create a new job"""
    user_id = get_jwt_identity()
    
    try:
        # Validate request data
        data = job_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'details': err.messages
        })), 400
    
    # Validate asset ownership if asset IDs provided
    if data.get('asset_ids'):
        assets = Asset.query.filter(
            and_(
                Asset.id.in_(data['asset_ids']),
                Asset.user_id == user_id
            )
        ).all()
        
        if len(assets) != len(data['asset_ids']):
            return jsonify(error_schema.dump({
                'message': 'One or more assets not found or not owned by user'
            })), 400
    
    # Create new job
    job = Job(
        title=data['title'],
        description=data.get('description'),
        job_type=JobType(data['job_type']),
        priority=JobPriority(data['priority']),
        user_id=user_id,
        parameters=data.get('parameters', {}),
        estimated_duration=data.get('estimated_duration')
    )
    
    db.session.add(job)
    db.session.flush()  # Get the job ID
    
    # Add assets to job if provided
    if data.get('asset_ids'):
        for asset in assets:
            job.add_asset(asset)
    
    db.session.commit()
    
    # Dispatch appropriate Celery task based on job type
    task_result = None
    if job.job_type == JobType.TEXT_TO_SPEECH:
        from ..tasks.tts_tasks import generate_speech
        # For TTS, we need a voice_clone_id (asset ID) instead of voice_sample string
        voice_asset_id = job.parameters.get('voice_asset_id')
        if not voice_asset_id and data.get('asset_ids'):
            # Use the first asset as the voice sample
            voice_asset_id = data['asset_ids'][0]
        
        if voice_asset_id:
            task_result = generate_speech.delay(
                job.id,
                job.parameters.get('text', ''),
                voice_asset_id
            )
        else:
            # No voice asset provided, mark job as failed
            job.status = JobStatus.FAILED
            job.progress_message = 'No voice sample provided'
    elif job.job_type == JobType.VOICE_CLONE:
        from ..tasks.voice_tasks import clone_voice_task
        task_result = clone_voice_task.delay(
            job.id,
            job.parameters.get('voice_sample_path', ''),
            user_id
        )
    elif job.job_type == JobType.VIDEO_GENERATION:
        from ..tasks.video_tasks import generate_video
        task_result = generate_video.delay(
            job.id,
            job.parameters.get('portrait_path', ''),
            job.parameters.get('audio_path', ''),
            user_id
        )
    elif job.job_type == JobType.SCRIPT_GENERATION:
        from ..tasks.llm_tasks import generate_script
        task_result = generate_script.delay(
            job.id,
            job.parameters.get('prompt', ''),
            topic=job.parameters.get('topic', ''),
            target_audience=job.parameters.get('target_audience', 'general'),
            duration_minutes=job.parameters.get('duration_minutes', 5),
            style=job.parameters.get('style', 'conversational'),
            additional_context=job.parameters.get('additional_context', '')
        )
    elif job.job_type == JobType.FULL_PIPELINE:
        from ..tasks.video_tasks import full_generation_pipeline
        task_result = full_generation_pipeline.delay(
            job.id,
            job.parameters,
            user_id
        )
    
    # Update job with task ID if task was started
    if task_result:
        job.celery_task_id = task_result.id
        db.session.commit()
    
    # Return created job
    response_data = job.to_dict(include_details=True)
    return jsonify({'job': response_data}), 201


@jobs_bp.route('/<int:job_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_job(job_id):
    """Get specific job details"""
    user_id = get_jwt_identity()
    
    # Get fresh job data from database
    job = get_fresh_job(job_id, user_id)
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    # Include job steps in the response
    job_dict = job.to_dict(include_details=True)
    job_dict['steps'] = [step.to_dict(include_details=True) for step in job.steps]
    
    return jsonify({'job': job_dict}), 200


@jobs_bp.route('/<int:job_id>', methods=['PUT'])
@jwt_required()
@handle_errors
def update_job(job_id):
    """Update job details"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    # Don't allow updates to completed/failed jobs
    if job.is_completed:
        return jsonify(error_schema.dump({
            'message': 'Cannot update completed or failed job'
        })), 400
    
    try:
        # Validate request data
        data = job_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'details': err.messages
        })), 400
    
    # Update job fields
    if 'title' in data:
        job.title = data['title']
    if 'description' in data:
        job.description = data['description']
    if 'priority' in data:
        job.priority = JobPriority(data['priority'])
    if 'parameters' in data:
        job.parameters = data['parameters']
    
    db.session.commit()
    
    response_data = job.to_dict(include_details=True)
    return jsonify({'job': response_data}), 200


@jobs_bp.route('/<int:job_id>/cancel', methods=['POST'])
@jwt_required()
@handle_errors
def cancel_job(job_id):
    """Cancel specific job"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    # Only allow cancellation of pending or processing jobs
    if job.status not in [JobStatus.PENDING, JobStatus.PROCESSING]:
        return jsonify(error_schema.dump({
            'message': 'Can only cancel pending or processing jobs'
        })), 400
    
    # Cancel the job
    job.status = JobStatus.CANCELLED
    job.completed_at = db.func.now()
    
    # Cancel any running steps
    for step in job.steps:
        if step.status == StepStatus.RUNNING:
            step.status = StepStatus.FAILED
            step.completed_at = db.func.now()
            step.error_info = {'message': 'Job was cancelled'}
    
    db.session.commit()
    
    return jsonify(message_schema.dump({
        'message': 'Job cancelled successfully'
    })), 200


@jobs_bp.route('/<int:job_id>/progress', methods=['PUT'])
@jwt_required()
@handle_errors
def update_job_progress(job_id):
    """Update job progress"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    try:
        # Validate request data
        data = job_progress_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'details': err.messages
        })), 400
    
    # Update progress
    job.update_progress(data['progress_percentage'], data.get('message'))
    db.session.commit()
    
    return jsonify(message_schema.dump({
        'message': 'Progress updated successfully'
    })), 200


@jobs_bp.route('/<int:job_id>/steps', methods=['GET'])
@jwt_required()
@handle_errors
def list_job_steps(job_id):
    """List steps for a specific job"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    steps_data = [step.to_dict(include_details=True) for step in job.steps]
    
    return jsonify({'steps': steps_data}), 200


@jobs_bp.route('/<int:job_id>/steps', methods=['POST'])
@jwt_required()
@handle_errors
def create_job_step(job_id):
    """Create a new step for a job"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    try:
        # Validate request data
        data = job_step_create_schema.load(request.json)
    except ValidationError as err:
        return jsonify(error_schema.dump({
            'message': 'Validation failed',
            'details': err.messages
        })), 400
    
    # Create new step
    step = JobStep(
        name=data['name'],
        description=data.get('description'),
        job_id=job.id,
        step_order=data['step_order'],
        estimated_duration=data.get('estimated_duration'),
        input_data=data.get('input_data', {})
    )
    
    db.session.add(step)
    db.session.commit()
    
    response_data = step.to_dict(include_details=True)
    return jsonify({'step': response_data}), 201


@jobs_bp.route('/<int:job_id>/status', methods=['GET'])
@jwt_required()
@handle_errors
def get_job_status(job_id):
    """Get real-time job status (optimized for monitoring)"""
    user_id = get_jwt_identity()
    
    # Get fresh job data from database
    job = get_fresh_job(job_id, user_id)
    
    if not job:
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    # Return minimal status information for monitoring
    return jsonify({
        'job_id': job.id,
        'status': job.status.value,
        'progress_percentage': job.progress_percentage,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'task_id': job.celery_task_id,
        'results': job.results
    }), 200


@jobs_bp.route('/<int:job_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_job(job_id):
    """Delete a job and all associated data"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🗑️ DELETE request received for job_id: {job_id}")
    
    user_id = get_jwt_identity()
    logger.info(f"👤 User ID from JWT: {user_id}")
    
    # Get job with ownership verification
    logger.info(f"🔍 Looking up job {job_id} for user {user_id}")
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
    if not job:
        logger.warning(f"❌ Job {job_id} not found for user {user_id}")
        return jsonify(error_schema.dump({
            'message': 'Job not found'
        })), 404
    
    logger.info(f"✅ Found job: {job.id}, status: {job.status}, celery_task_id: {job.celery_task_id}")
    
    # Check if job can be deleted (should not be processing)
    if job.status == JobStatus.PROCESSING:
        logger.warning(f"⚠️ Cannot delete processing job {job_id}")
        return jsonify(error_schema.dump({
            'message': 'Cannot delete a processing job. Cancel it first.'
        })), 400
    
    logger.info(f"🚀 Passed running check, starting deletion process")
    try:
        logger.info(f"📋 Entered try block for job deletion")
        
        # If job has a Celery task and it's still pending, revoke it
        if job.celery_task_id and job.status == JobStatus.PENDING:
            logger.info(f"📋 Attempting to revoke Celery task: {job.celery_task_id}")
            try:
                from ..tasks import celery
                celery.control.revoke(job.celery_task_id, terminate=True)
                logger.info(f"✅ Celery task {job.celery_task_id} revoked successfully")
            except ImportError as import_err:
                logger.warning(f"⚠️ Could not import celery to revoke task {job.celery_task_id}: {import_err}")
            except Exception as celery_error:
                logger.warning(f"⚠️ Could not revoke celery task {job.celery_task_id}: {celery_error}")
        
        # Delete job steps first (due to foreign key constraints)
        logger.info(f"🔗 Checking job steps for job {job_id}")
        job_steps_count = JobStep.query.filter_by(job_id=job.id).count()
        logger.info(f"📊 Found {job_steps_count} job steps to delete")
        
        if job_steps_count > 0:
            deleted_steps = JobStep.query.filter_by(job_id=job.id).delete()
            logger.info(f"🗑️ Deleted {deleted_steps} job steps")
        
        # Delete the job itself
        logger.info(f"🗑️ Deleting job {job_id}")
        db.session.delete(job)
        
        logger.info(f"💾 Committing transaction")
        db.session.commit()
        
        logger.info(f"✅ Job {job_id} deleted successfully")
        return jsonify(message_schema.dump({
            'message': f'Job {job_id} deleted successfully'
        })), 200
        
    except Exception as e:
        logger.error(f"❌ Error deleting job {job_id}: {str(e)}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        logger.error(f"📋 Error details: {repr(e)}")
        
        # Add full traceback for debugging
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        
        db.session.rollback()
        logger.info(f"🔄 Database transaction rolled back")
        
        print(f"Error deleting job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify(error_schema.dump({
            'message': f'Failed to delete job: {str(e)}'
        })), 500
