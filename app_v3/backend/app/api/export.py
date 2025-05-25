"""
Export API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

export_bp = Blueprint('export', __name__)


@export_bp.route('/video/<int:video_id>/<format>', methods=['GET'])
@jwt_required()
def export_video(video_id, format):
    """Export video in specified format"""
    # TODO: Implement video export
    return jsonify({'message': f'Export video {video_id} as {format} - coming soon'}), 501


@export_bp.route('/scorm/<int:video_id>', methods=['POST'])
@jwt_required()
def export_scorm(video_id):
    """Export video as SCORM package"""
    # TODO: Implement SCORM export
    return jsonify({'message': f'Export video {video_id} as SCORM - coming soon'}), 501
