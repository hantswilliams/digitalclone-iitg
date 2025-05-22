"""
API Routes for the application
"""
from flask import request, jsonify, current_app, session, url_for
from werkzeug.utils import secure_filename
from app.api import api_bp
from app.models import Text, Photo, Audio, Video, PowerPoint, User
from app.extensions import db
from app.services.audio_service import AudioService
from app.services.video_service import VideoService
from app.services.presentation_service import PresentationService
from app.services.project_service import ProjectService
from app.services.storage_service import StorageService
from app.tasks.audio_tasks import generate_audio_task
from app.tasks.video_tasks import generate_video_task
from app.tasks.presentation_tasks import create_presentation_task, create_scorm_task
from app.utils.api import api_response, api_error, handle_api_exception, login_required
from app.errors import APIError
import os
import uuid
import datetime


@api_bp.route('/status')
def status():
    """API status check endpoint"""
    return api_response(
        success=True,
        data={
            'status': 'ok',
            'timestamp': datetime.datetime.now().isoformat(),
            'version': '2.0.0'
        }
    )


@api_bp.route('/texts', methods=['GET'])
@handle_api_exception
@login_required
def get_texts():
    """Get texts for the current user"""
    user_id = session['user'].get('sub')
    texts = Text.query.filter_by(user_id=user_id).all()
    
    return api_response(
        success=True,
        data={
            'texts': [{
                'id': text.id,
                'text_content': text.text_content,
                'created_at': text.created_at.isoformat()
            } for text in texts]
        }
    )


@api_bp.route('/texts', methods=['POST'])
@handle_api_exception
@login_required
def create_text():
    """Create a new text entry"""
    data = request.get_json()
    if not data:
        raise APIError('No data provided', 400)
    
    if 'text_content' not in data or not data['text_content'].strip():
        raise APIError('Missing required field: text_content', 400)
    
    user_id = session['user'].get('sub')
    try:
        text = Text(user_id=user_id, text_content=data['text_content'])
        
        db.session.add(text)
        db.session.commit()
        
        return api_response(
            success=True,
            message='Text created successfully',
            data={
                'text': {
                    'id': text.id,
                    'text_content': text.text_content,
                    'created_at': text.created_at.isoformat()
                }
            },
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating text: {str(e)}")
        raise APIError('Failed to create text', 500)


@api_bp.route('/photos', methods=['GET'])
@handle_api_exception
@login_required
def get_photos():
    """Get photos for the current user"""
    user_id = session['user'].get('sub')
    photos = Photo.query.filter_by(user_id=user_id).all()
    
    return api_response(
        success=True,
        data={
            'photos': [{
                'id': photo.id,
                'photo_url': photo.photo_url,
                'photo_description': photo.photo_description,
                'created_at': photo.created_at.isoformat()
            } for photo in photos]
        }
    )


@api_bp.route('/photos', methods=['POST'])
def upload_photo():
    """Upload a new photo"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    # Save file and upload to S3
    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    user_id = session['user'].get('sub')
    description = request.form.get('description', '')
    
    # Upload to S3
    storage_service = StorageService()
    s3_filename = storage_service.upload_image(filename, file_path)
    
    if not s3_filename:
        return jsonify({'error': 'Failed to upload image'}), 500
    
    # Create photo record
    photo_url = f"https://{current_app.config['S3_BUCKET_NAME']}.s3.amazonaws.com/{s3_filename}"
    photo = Photo(user_id=user_id, photo_url=photo_url, photo_description=description)
    
    db.session.add(photo)
    db.session.commit()
    
    # Clean up local file
    os.remove(file_path)
    
    return jsonify({
        'success': True,
        'photo': {
            'id': photo.id,
            'photo_url': photo_url,
            'photo_description': description,
            'created_at': photo.created_at.isoformat()
        }
    }), 201


@api_bp.route('/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from text"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
    
    required_fields = ['text_id', 'voice']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    
    user_id = session['user'].get('sub')
    provider = data.get('provider', 'playht')
    
    # Start async task for audio generation
    task = generate_audio_task.delay(
        data['text_id'],
        data['voice'],
        provider,
        user_id
    )
    
    return jsonify({
        'success': True,
        'task_id': task.id,
        'status': 'processing'
    })


@api_bp.route('/generate-video', methods=['POST'])
def generate_video():
    """Generate video from photo and audio"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
    
    required_fields = ['photo_id', 'audio_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    
    user_id = session['user'].get('sub')
    provider = data.get('provider', 'sadtalker')
    
    # Extract optional parameters for video generation
    kwargs = {
        'preprocess': data.get('preprocess', 'resize'),
        'still_mode': data.get('still_mode', True),
        'use_enhancer': data.get('use_enhancer', True),
        'pose_style': data.get('pose_style', 0),
        'size': data.get('size', 512),
        'expression_scale': data.get('expression_scale', 1)
    }
    
    # Start async task for video generation
    task = generate_video_task.delay(
        data['photo_id'],
        data['audio_id'],
        provider,
        user_id,
        **kwargs
    )
    
    return jsonify({
        'success': True,
        'task_id': task.id,
        'status': 'processing'
    })


@api_bp.route('/create-presentation', methods=['POST'])
def create_presentation():
    """Create presentation from slides data"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
    
    required_fields = ['title', 'slides']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    
    user_id = session['user'].get('sub')
    
    # Start async task for presentation creation
    task = create_presentation_task.delay(
        data['title'],
        data['slides'],
        user_id
    )
    
    return jsonify({
        'success': True,
        'task_id': task.id,
        'status': 'processing'
    })


@api_bp.route('/create-scorm', methods=['POST'])
def create_scorm():
    """Create SCORM package from presentation"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request data'}), 400
    
    required_fields = ['presentation_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
    
    user_id = session['user'].get('sub')
    
    # Start async task for SCORM package creation
    task = create_scorm_task.delay(
        data['presentation_id'],
        data.get('title'),
        data.get('metadata'),
        user_id
    )
    
    return jsonify({
        'success': True,
        'task_id': task.id,
        'status': 'processing'
    })


@api_bp.route('/tasks/<task_id>')
@handle_api_exception
def get_task_status(task_id):
    """Check status of a background task"""
    if not task_id:
        raise APIError('Task ID is required', 400)
    
    from app.utils.tasks import get_task_status
    task_info = get_task_status(task_id)
    
    return api_response(
        success=True,
        data=task_info
    )


@api_bp.route('/projects', methods=['GET', 'POST'])
def projects():
    """Get or create projects"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user'].get('sub')
    project_service = ProjectService()
    
    if request.method == 'GET':
        result = project_service.get_projects(user_id)
        return jsonify(result)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        result = project_service.create_project(
            user_id,
            data['name'],
            data.get('description', '')
        )
        
        status_code = 201 if result['success'] else 400
        return jsonify(result), status_code


@api_bp.route('/projects/<int:project_id>', methods=['GET', 'PUT', 'DELETE'])
def project(project_id):
    """Get, update or delete a specific project"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    user_id = session['user'].get('sub')
    project_service = ProjectService()
    
    if request.method == 'GET':
        result = project_service.get_project(project_id, user_id)
        if not result['success']:
            return jsonify(result), 404
        return jsonify(result)
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request data'}), 400
        
        result = project_service.update_project(project_id, user_id, data)
        if not result['success']:
            return jsonify(result), 404
        return jsonify(result)
    
    elif request.method == 'DELETE':
        result = project_service.delete_project(project_id, user_id)
        if not result['success']:
            return jsonify(result), 404
        return jsonify(result)


@api_bp.route('/projects/<int:project_id>/media', methods=['POST', 'DELETE'])
def project_media(project_id):
    """Add or remove media from a project"""
    if 'user' not in session:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    if not data or 'media_type' not in data or 'media_id' not in data:
        return jsonify({'error': 'Missing required fields: media_type, media_id'}), 400
    
    user_id = session['user'].get('sub')
    project_service = ProjectService()
    
    if request.method == 'POST':
        result = project_service.add_to_project(
            project_id,
            user_id,
            data['media_type'],
            data['media_id']
        )
    elif request.method == 'DELETE':
        result = project_service.remove_from_project(
            project_id,
            user_id,
            data['media_type'],
            data['media_id']
        )
    
    if not result['success']:
        status_code = 404 if 'not found' in result.get('error', '') else 400
        return jsonify(result), status_code
    
    return jsonify(result)


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())
