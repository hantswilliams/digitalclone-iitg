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
    
    # Return created job
    response_data = job.to_dict(include_details=True)
    return jsonify({'job': response_data}), 201


@jobs_bp.route('/<int:job_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_job(job_id):
    """Get specific job details"""
    user_id = get_jwt_identity()
    
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    
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
