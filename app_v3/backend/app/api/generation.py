"""
Video generation API endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import Schema, fields, ValidationError

from ..extensions import db
from ..models import Job, Asset, User
from ..models.asset import AssetType, AssetStatus
from ..models.job import JobType, JobStatus, JobPriority
from ..tasks import generate_speech, validate_tts_service, generate_video, validate_video_service

generation_bp = Blueprint('generation', __name__)


class TTSRequestSchema(Schema):
    """Schema for text-to-speech requests."""
    text = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0, 
                     error_messages={'required': 'Text is required for speech generation'})
    voice_asset_id = fields.Int(required=True, 
                               error_messages={'required': 'Voice asset ID is required'})
    speaking_rate = fields.Float(load_default=15.0, validate=lambda x: 5.0 <= x <= 50.0,
                                error_messages={'invalid': 'Speaking rate must be between 5.0 and 50.0'})
    priority = fields.Str(load_default='normal', validate=lambda x: x in ['low', 'normal', 'high', 'urgent'])


class VideoRequestSchema(Schema):
    """Schema for video generation requests."""
    portrait_asset_id = fields.Int(required=True,
                                  error_messages={'required': 'Portrait asset ID is required'})
    audio_asset_id = fields.Int(required=True,
                               error_messages={'required': 'Audio asset ID is required'})
    enhancer = fields.Str(load_default='gfpgan', validate=lambda x: x in ['gfpgan', 'RestoreFormer'])
    face_enhance = fields.Bool(load_default=True)
    background_enhance = fields.Bool(load_default=True)
    preprocess = fields.Str(load_default='crop', validate=lambda x: x in ['crop', 'resize', 'full', 'extcrop', 'extfull'])
    fps = fields.Int(load_default=25, validate=lambda x: 15 <= x <= 60)
    use_blink = fields.Bool(load_default=True)
    exp_scale = fields.Float(load_default=1.0, validate=lambda x: 0.1 <= x <= 2.0)
    priority = fields.Str(load_default='normal', validate=lambda x: x in ['low', 'normal', 'high', 'urgent'])


class ServiceStatusSchema(Schema):
    """Schema for service status responses."""
    service = fields.Str()
    status = fields.Str()
    details = fields.Dict()


@generation_bp.route('/script', methods=['POST'])
@jwt_required()
def generate_script():
    """Generate script using LLM"""
    # TODO: Implement script generation
    return jsonify({'message': 'Script generation endpoint - coming soon'}), 501


@generation_bp.route('/voice-clone', methods=['POST'])
@jwt_required()
def clone_voice():
    """Clone voice from reference audio"""
    # TODO: Implement voice cloning
    return jsonify({'message': 'Voice cloning endpoint - coming soon'}), 501


@generation_bp.route('/text-to-speech', methods=['POST'])
@jwt_required()
def text_to_speech():
    """
    Convert text to speech using voice cloning.
    
    Request body:
    {
        "text": "Text to convert to speech",
        "voice_asset_id": 123,
        "speaking_rate": 15.0,  // optional, default 15.0
        "priority": "normal"    // optional, default "normal"
    }
    
    Returns:
    {
        "job_id": 456,
        "status": "pending",
        "message": "Text-to-speech job created successfully"
    }
    """
    try:
        # Validate request data
        schema = TTSRequestSchema()
        data = schema.load(request.get_json() or {})
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate voice asset exists and belongs to user
        voice_asset = Asset.query.filter_by(
            id=data['voice_asset_id'],
            user_id=user_id,
            asset_type='voice_sample'
        ).first()
        
        if not voice_asset:
            return jsonify({
                'error': 'Voice asset not found or not accessible'
            }), 404
        
        if voice_asset.status != AssetStatus.READY:
            return jsonify({
                'error': f'Voice asset is not ready (status: {voice_asset.status.value})'
            }), 400
        
        # Create job for TTS generation
        job = Job(
            title=f"Text-to-Speech: {voice_asset.original_filename}",
            user_id=user_id,
            job_type=JobType.TEXT_TO_SPEECH,
            status=JobStatus.PENDING,
            priority=JobPriority(data['priority']),
            parameters={
                'text': data['text'],
                'voice_asset_id': data['voice_asset_id'],
                'speaking_rate': data['speaking_rate'],
                'text_length': len(data['text'])
            },
            description=f"Generate speech: '{data['text'][:50]}{'...' if len(data['text']) > 50 else ''}'"
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Queue the speech generation task
        task = generate_speech.apply_async(
            args=[job.id, data['text'], data['voice_asset_id']],
            priority=_get_task_priority(data['priority'])
        )
        
        # Update job with task ID
        job.task_id = task.id
        db.session.commit()
        
        return jsonify({
            'job_id': job.id,
            'task_id': task.id,
            'status': job.status.value,
            'message': 'Text-to-speech job created successfully',
            'estimated_duration': len(data['text']) * 0.1  # Rough estimate in seconds
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create TTS job: {str(e)}'}), 500


@generation_bp.route('/tts/status', methods=['GET'])
@jwt_required()
def tts_service_status():
    """
    Check the status of the TTS service (Zyphra).
    
    Returns:
    {
        "service": "zyphra_tts",
        "status": "healthy|unhealthy|error",
        "details": {...}
    }
    """
    try:
        # Queue validation task
        task = validate_tts_service.apply_async()
        result = task.get(timeout=30)  # Wait up to 30 seconds
        
        return jsonify({
            'service': 'zyphra_tts',
            'status': result['status'],
            'details': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'service': 'zyphra_tts',
            'status': 'error',
            'details': {'error': str(e)}
        }), 500


def _get_task_priority(priority_str: str) -> int:
    """Convert priority string to Celery task priority number."""
    priority_map = {
        'low': 3,
        'normal': 5,
        'high': 7,
        'urgent': 9
    }
    return priority_map.get(priority_str, 5)


@generation_bp.route('/video', methods=['POST'])
@jwt_required()
def generate_video_endpoint():
    """
    Generate talking-head video from portrait image and audio.
    
    Request body:
    {
        "portrait_asset_id": 123,
        "audio_asset_id": 456,
        "enhancer": "gfpgan",        // optional, default "gfpgan"
        "face_enhance": true,        // optional, default true
        "background_enhance": true,  // optional, default true
        "preprocess": "crop",        // optional, default "crop"
        "fps": 25,                   // optional, default 25
        "use_blink": true,          // optional, default true
        "exp_scale": 1.0,           // optional, default 1.0
        "priority": "normal"         // optional, default "normal"
    }
    
    Returns:
    {
        "job_id": 789,
        "status": "pending",
        "message": "Video generation job created successfully"
    }
    """
    try:
        # Validate request data
        schema = VideoRequestSchema()
        data = schema.load(request.get_json() or {})
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Validate portrait asset exists and belongs to user
        portrait_asset = Asset.query.filter_by(
            id=data['portrait_asset_id'],
            user_id=user_id,
            asset_type=AssetType.PORTRAIT
        ).first()
        
        # Debug logging
        current_app.logger.info(f"Looking for portrait asset: id={data['portrait_asset_id']}, user_id={user_id}")
        if not portrait_asset:
            # Additional debug: check if asset exists without user filter
            debug_asset = Asset.query.filter_by(id=data['portrait_asset_id']).first()
            if debug_asset:
                current_app.logger.error(f"Asset exists but user mismatch: asset.user_id={debug_asset.user_id}, request.user_id={user_id}, asset.type={debug_asset.asset_type}")
            else:
                current_app.logger.error(f"Asset does not exist: id={data['portrait_asset_id']}")
            
            return jsonify({
                'error': 'Portrait asset not found or not accessible'
            }), 404
        
        if portrait_asset.status != AssetStatus.READY:
            return jsonify({
                'error': f'Portrait asset is not ready (status: {portrait_asset.status.value})'
            }), 400
        
        # Validate audio asset exists and belongs to user
        audio_asset = Asset.query.filter_by(
            id=data['audio_asset_id'],
            user_id=user_id
        ).first()
        
        # Audio can be either voice_sample or generated TTS audio
        if not audio_asset or audio_asset.asset_type not in [AssetType.VOICE_SAMPLE, AssetType.GENERATED_AUDIO]:
            return jsonify({
                'error': 'Audio asset not found or not accessible'
            }), 404
        
        if audio_asset.status != AssetStatus.READY:
            return jsonify({
                'error': f'Audio asset is not ready (status: {audio_asset.status.value})'
            }), 400
        
        # Create job for video generation
        job = Job(
            title=f"Video Generation: {portrait_asset.original_filename}",
            user_id=user_id,
            job_type=JobType.VIDEO_GENERATION,
            status=JobStatus.PENDING,
            priority=JobPriority(data['priority']),
            parameters={
                'portrait_asset_id': data['portrait_asset_id'],
                'audio_asset_id': data['audio_asset_id'],
                'enhancer': data['enhancer'],
                'face_enhance': data['face_enhance'],
                'background_enhance': data['background_enhance'],
                'preprocess': data['preprocess'],
                'fps': data['fps'],
                'use_blink': data['use_blink'],
                'exp_scale': data['exp_scale']
            },
            description=f"Generate talking-head video from portrait {portrait_asset.filename}"
        )
        
        db.session.add(job)
        db.session.commit()
        
        # Queue the video generation task
        task = generate_video.apply_async(
            args=[job.id, data['portrait_asset_id'], data['audio_asset_id']],
            priority=_get_task_priority(data['priority'])
        )
        
        # Update job with task ID
        job.task_id = task.id
        db.session.commit()
        
        return jsonify({
            'job_id': job.id,
            'task_id': task.id,
            'status': job.status.value,
            'message': 'Video generation job created successfully',
            'estimated_duration': 60  # Rough estimate in seconds for video generation
        }), 201
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.messages}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to create video generation job: {str(e)}'}), 500


@generation_bp.route('/video/status', methods=['GET'])
@jwt_required()
def video_service_status():
    """
    Check the status of the video generation service (KDTalker).
    
    Returns:
    {
        "service": "kdtalker",
        "status": "healthy|unhealthy|error",
        "details": {...}
    }
    """
    try:
        # Queue validation task
        task = validate_video_service.apply_async()
        result = task.get(timeout=30)  # Wait up to 30 seconds
        
        return jsonify({
            'service': 'kdtalker',
            'status': result['status'],
            'details': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'service': 'kdtalker',
            'status': 'error',
            'details': {'error': str(e)}
        }), 500


@generation_bp.route('/full-pipeline', methods=['POST'])
@jwt_required()
def full_pipeline():
    """Run complete generation pipeline"""
    # TODO: Implement full pipeline
    return jsonify({'message': 'Full pipeline endpoint - coming soon'}), 501
