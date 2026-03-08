"""
Content Detection API route
POST /api/content/detect  →  { subject, content_type, subject_confidence, content_type_confidence }
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from services.content_service import ContentDetectionService

content_bp = Blueprint('content', __name__)


@content_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect_content():
    """
    Detect subject and content type from a screen capture.

    Expected JSON body:
    {
        "screen_data": "<base64-encoded JPEG/PNG screenshot>"
    }

    Returns:
    {
        "subject":                "Mathematics",
        "content_type":           "Quiz",
        "subject_confidence":     0.82,
        "content_type_confidence": 0.71
    }
    """
    try:
        data = request.get_json()

        if not data or 'screen_data' not in data:
            return jsonify({'error': 'screen_data is required'}), 400

        screen_data = data['screen_data']
        if not screen_data:
            return jsonify({'error': 'screen_data must not be empty'}), 400

        service = ContentDetectionService.get_instance()
        result  = service.detect(screen_data)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
