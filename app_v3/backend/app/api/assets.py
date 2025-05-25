"""
Asset management API endpoints
"""
import os
import uuid
import mimetypes
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy import and_

from ..extensions import db
from ..models.asset import Asset, AssetType, AssetStatus
from ..models.user import User
from ..schemas import (
    AssetUploadSchema, AssetResponseSchema, AssetListSchema,
    PresignedUrlSchema, PresignedUrlResponseSchema
)
from ..services.storage import storage_service
from ..utils import handle_errors

assets_bp = Blueprint('assets', __name__)

# File validation constants
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
ALLOWED_SCRIPT_EXTENSIONS = {'.txt', '.md', '.json'}

MAX_FILE_SIZES = {
    'portrait': 10 * 1024 * 1024,      # 10MB for images
    'voice_sample': 50 * 1024 * 1024,  # 50MB for audio
    'script': 1 * 1024 * 1024          # 1MB for scripts
}


def validate_file_upload(file, asset_type):
    """Validate uploaded file"""
    if not file or not file.filename:
        return False, "No file provided"
    
    # Get file extension
    filename = file.filename.lower()
    file_ext = os.path.splitext(filename)[1]
    
    # Validate file extension based on asset type
    if asset_type == 'portrait':
        if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            return False, f"Invalid image format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
    elif asset_type == 'voice_sample':
        if file_ext not in ALLOWED_AUDIO_EXTENSIONS:
            return False, f"Invalid audio format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
    elif asset_type == 'script':
        if file_ext not in ALLOWED_SCRIPT_EXTENSIONS:
            return False, f"Invalid script format. Allowed: {', '.join(ALLOWED_SCRIPT_EXTENSIONS)}"
    else:
        return False, "Invalid asset type"
    
    # Check file size (rough estimate from content length)
    max_size = MAX_FILE_SIZES.get(asset_type, 10 * 1024 * 1024)
    if hasattr(file, 'content_length') and file.content_length:
        if file.content_length > max_size:
            return False, f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB"
    
    return True, None


def generate_storage_path(user_id, asset_type, filename):
    """Generate storage path for asset"""
    # Create unique filename to avoid conflicts
    unique_id = str(uuid.uuid4())
    file_ext = os.path.splitext(filename)[1]
    unique_filename = f"{unique_id}{file_ext}"
    
    # Create hierarchical path: user_id/asset_type/unique_filename
    return f"users/{user_id}/{asset_type}/{unique_filename}"


@assets_bp.route('/', methods=['GET'])
@jwt_required()
@handle_errors
def list_assets():
    """List user's assets with optional filtering"""
    user_id = get_jwt_identity()
    
    # Validate query parameters
    schema = AssetListSchema()
    try:
        filters = schema.load(request.args)
    except ValidationError as e:
        return jsonify({'error': 'Invalid query parameters', 'details': e.messages}), 400
    
    # Build query
    query = Asset.query.filter(Asset.user_id == user_id)
    
    # Apply filters
    if filters.get('asset_type'):
        query = query.filter(Asset.asset_type == AssetType(filters['asset_type']))
    
    if filters.get('status'):
        query = query.filter(Asset.status == AssetStatus(filters['status']))
    
    # Apply pagination
    page = filters.get('page', 1)
    per_page = filters.get('per_page', 20)
    
    try:
        paginated = query.order_by(Asset.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    except Exception as e:
        current_app.logger.error(f"Asset listing error: {str(e)}")
        return jsonify({'error': 'Failed to retrieve assets'}), 500
    
    # Serialize assets with download URLs
    response_schema = AssetResponseSchema()
    assets_data = []
    
    for asset in paginated.items:
        asset_dict = asset.to_dict()
        
        # Add signed URLs for ready assets
        if asset.status == AssetStatus.READY:
            download_url = storage_service.get_presigned_url(
                asset.storage_path, 
                bucket_name=asset.storage_bucket,
                method='GET'
            )
            asset_dict['download_url'] = download_url
            
            # For images, also provide a preview URL (same as download for now)
            if asset.is_image:
                asset_dict['preview_url'] = download_url
        
        assets_data.append(asset_dict)
    
    return jsonify({
        'assets': assets_data,
        'pagination': {
            'page': paginated.page,
            'pages': paginated.pages,
            'per_page': paginated.per_page,
            'total': paginated.total,
            'has_next': paginated.has_next,
            'has_prev': paginated.has_prev
        }
    }), 200


@assets_bp.route('/upload', methods=['POST'])
@jwt_required()
@handle_errors
def upload_asset():
    """Upload new asset file"""
    user_id = get_jwt_identity()
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get asset type from form data
    asset_type = request.form.get('asset_type')
    if not asset_type:
        return jsonify({'error': 'Asset type is required'}), 400
    
    # Validate asset type
    try:
        asset_type_enum = AssetType(asset_type)
    except ValueError:
        return jsonify({'error': 'Invalid asset type'}), 400
    
    # Validate file upload
    is_valid, error_msg = validate_file_upload(file, asset_type)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Get additional metadata
    description = request.form.get('description', '')
    
    # Generate storage path and filename
    original_filename = file.filename
    storage_path = generate_storage_path(user_id, asset_type, original_filename)
    bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
    
    # Get file metadata
    file_size = 0
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)     # Reset to beginning
    
    mime_type, _ = mimetypes.guess_type(original_filename)
    if not mime_type:
        mime_type = file.content_type or 'application/octet-stream'
    
    file_extension = os.path.splitext(original_filename)[1].lower()
    
    # Create asset record in database
    try:
        asset = Asset(
            filename=os.path.basename(storage_path),
            original_filename=original_filename,
            asset_type=asset_type_enum,
            storage_path=storage_path,
            storage_bucket=bucket_name,
            user_id=user_id,
            file_size=file_size,
            mime_type=mime_type,
            file_extension=file_extension,
            status=AssetStatus.UPLOADING,
            asset_metadata={'description': description} if description else None
        )
        
        db.session.add(asset)
        db.session.commit()
        
        # Upload file to storage
        upload_result = storage_service.upload_file(
            file_data=file,
            object_name=storage_path,
            bucket_name=bucket_name,
            content_type=mime_type
        )
        
        if upload_result['success']:
            # Update asset status to ready
            asset.status = AssetStatus.READY
            asset.asset_metadata = asset.asset_metadata or {}
            asset.asset_metadata.update({
                'etag': upload_result.get('etag'),
                'version_id': upload_result.get('version_id')
            })
            db.session.commit()
            
            current_app.logger.info(f"Asset uploaded successfully: {asset.id}")
            
            # Return asset data with download URL
            asset_dict = asset.to_dict()
            asset_dict['download_url'] = storage_service.get_presigned_url(
                storage_path, bucket_name=bucket_name, method='GET'
            )
            
            return jsonify({
                'message': 'Asset uploaded successfully',
                'asset': asset_dict
            }), 201
            
        else:
            # Upload failed, update status and cleanup
            asset.status = AssetStatus.ERROR
            asset.processing_info = {'error': upload_result.get('error')}
            db.session.commit()
            
            return jsonify({
                'error': 'Failed to upload file to storage',
                'details': upload_result.get('error')
            }), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Asset upload error: {str(e)}")
        return jsonify({'error': 'Failed to process upload'}), 500


@assets_bp.route('/presigned-upload', methods=['POST'])
@jwt_required()
@handle_errors
def get_presigned_upload_url():
    """Get presigned URL for direct file upload"""
    user_id = get_jwt_identity()
    
    # Validate request data
    schema = PresignedUrlSchema()
    try:
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({'error': 'Invalid request data', 'details': e.messages}), 400
    
    filename = data['filename']
    asset_type = data['asset_type']
    file_size = data['file_size']
    content_type = data['content_type']
    
    # Validate asset type
    try:
        asset_type_enum = AssetType(asset_type)
    except ValueError:
        return jsonify({'error': 'Invalid asset type'}), 400
    
    # Validate file size
    max_size = MAX_FILE_SIZES.get(asset_type, 10 * 1024 * 1024)
    if file_size > max_size:
        return jsonify({
            'error': f'File too large. Maximum size: {max_size / (1024*1024):.1f}MB'
        }), 400
    
    # Validate file extension
    file_ext = os.path.splitext(filename.lower())[1]
    if asset_type == 'portrait' and file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({
            'error': f'Invalid image format. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
        }), 400
    elif asset_type == 'voice_sample' and file_ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({
            'error': f'Invalid audio format. Allowed: {", ".join(ALLOWED_AUDIO_EXTENSIONS)}'
        }), 400
    elif asset_type == 'script' and file_ext not in ALLOWED_SCRIPT_EXTENSIONS:
        return jsonify({
            'error': f'Invalid script format. Allowed: {", ".join(ALLOWED_SCRIPT_EXTENSIONS)}'
        }), 400
    
    # Generate storage path
    storage_path = generate_storage_path(user_id, asset_type, filename)
    bucket_name = current_app.config.get('MINIO_BUCKET_NAME')
    
    # Create asset record with UPLOADING status
    try:
        asset = Asset(
            filename=os.path.basename(storage_path),
            original_filename=filename,
            asset_type=asset_type_enum,
            storage_path=storage_path,
            storage_bucket=bucket_name,
            user_id=user_id,
            file_size=file_size,
            mime_type=content_type,
            file_extension=file_ext,
            status=AssetStatus.UPLOADING
        )
        
        db.session.add(asset)
        db.session.commit()
        
        # Generate presigned upload URL
        upload_url = storage_service.get_presigned_url(
            storage_path,
            bucket_name=bucket_name,
            method='PUT'
        )
        
        if upload_url:
            return jsonify({
                'upload_url': upload_url,
                'asset_id': asset.id,
                'expires_in': 3600,  # 1 hour
                'method': 'PUT',
                'headers': {
                    'Content-Type': content_type
                }
            }), 200
        else:
            # Cleanup asset record if URL generation failed
            db.session.delete(asset)
            db.session.commit()
            return jsonify({'error': 'Failed to generate upload URL'}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Presigned URL error: {str(e)}")
        return jsonify({'error': 'Failed to prepare upload'}), 500


@assets_bp.route('/<int:asset_id>/confirm-upload', methods=['POST'])
@jwt_required()
@handle_errors
def confirm_upload(asset_id):
    """Confirm that presigned upload completed successfully"""
    user_id = get_jwt_identity()
    
    # Get asset
    asset = Asset.query.filter(
        and_(Asset.id == asset_id, Asset.user_id == user_id)
    ).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    if asset.status != AssetStatus.UPLOADING:
        return jsonify({'error': 'Asset is not in uploading state'}), 400
    
    # Verify file exists in storage
    if storage_service.file_exists(asset.storage_path, asset.storage_bucket):
        # Get file metadata from storage
        file_info = storage_service.get_object_info(asset.storage_path, asset.storage_bucket)
        
        if file_info:
            # Update asset with actual file information
            asset.file_size = file_info['size']
            asset.status = AssetStatus.READY
            asset.asset_metadata = asset.asset_metadata or {}
            asset.asset_metadata.update({
                'etag': file_info['etag'],
                'confirmed_at': str(file_info['last_modified'])
            })
            db.session.commit()
            
            # Return updated asset data
            asset_dict = asset.to_dict()
            asset_dict['download_url'] = storage_service.get_presigned_url(
                asset.storage_path, bucket_name=asset.storage_bucket, method='GET'
            )
            
            return jsonify({
                'message': 'Upload confirmed successfully',
                'asset': asset_dict
            }), 200
        else:
            asset.status = AssetStatus.ERROR
            asset.processing_info = {'error': 'File verification failed'}
            db.session.commit()
            return jsonify({'error': 'File verification failed'}), 500
    else:
        asset.status = AssetStatus.ERROR
        asset.processing_info = {'error': 'File not found in storage'}
        db.session.commit()
        return jsonify({'error': 'Upload verification failed'}), 400


@assets_bp.route('/<int:asset_id>', methods=['GET'])
@jwt_required()
@handle_errors
def get_asset(asset_id):
    """Get specific asset details"""
    user_id = get_jwt_identity()
    
    # Get asset belonging to current user
    asset = Asset.query.filter(
        and_(Asset.id == asset_id, Asset.user_id == user_id)
    ).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    # Serialize asset data
    asset_dict = asset.to_dict()
    
    # Add signed URLs for ready assets
    if asset.status == AssetStatus.READY:
        download_url = storage_service.get_presigned_url(
            asset.storage_path, 
            bucket_name=asset.storage_bucket,
            method='GET'
        )
        asset_dict['download_url'] = download_url
        
        # For images, also provide a preview URL
        if asset.is_image:
            asset_dict['preview_url'] = download_url
    
    return jsonify({'asset': asset_dict}), 200


@assets_bp.route('/<int:asset_id>', methods=['DELETE'])
@jwt_required()
@handle_errors
def delete_asset(asset_id):
    """Delete specific asset"""
    user_id = get_jwt_identity()
    
    # Get asset belonging to current user
    asset = Asset.query.filter(
        and_(Asset.id == asset_id, Asset.user_id == user_id)
    ).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    try:
        # Delete file from storage
        storage_deleted = storage_service.delete_file(
            asset.storage_path, 
            bucket_name=asset.storage_bucket
        )
        
        if storage_deleted:
            current_app.logger.info(f"File deleted from storage: {asset.storage_path}")
        else:
            current_app.logger.warning(f"Failed to delete file from storage: {asset.storage_path}")
        
        # Delete asset record from database
        db.session.delete(asset)
        db.session.commit()
        
        current_app.logger.info(f"Asset deleted successfully: {asset_id}")
        
        return jsonify({
            'message': 'Asset deleted successfully',
            'asset_id': asset_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Asset deletion error: {str(e)}")
        return jsonify({'error': 'Failed to delete asset'}), 500


@assets_bp.route('/<int:asset_id>/download', methods=['GET'])
@jwt_required()
@handle_errors
def download_asset(asset_id):
    """Get download URL for asset"""
    user_id = get_jwt_identity()
    
    # Get asset belonging to current user
    asset = Asset.query.filter(
        and_(Asset.id == asset_id, Asset.user_id == user_id)
    ).first()
    
    if not asset:
        return jsonify({'error': 'Asset not found'}), 404
    
    if asset.status != AssetStatus.READY:
        return jsonify({'error': 'Asset is not ready for download'}), 400
    
    # Generate download URL
    download_url = storage_service.get_presigned_url(
        asset.storage_path,
        bucket_name=asset.storage_bucket,
        method='GET'
    )
    
    if download_url:
        return jsonify({
            'download_url': download_url,
            'filename': asset.original_filename,
            'expires_in': 3600
        }), 200
    else:
        return jsonify({'error': 'Failed to generate download URL'}), 500
