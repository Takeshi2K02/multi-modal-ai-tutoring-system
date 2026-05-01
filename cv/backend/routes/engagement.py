from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import EngagementLog
from services.engagement_service import process_engagement_data
from datetime import datetime

engagement_bp = Blueprint('engagement', __name__)

@engagement_bp.route('/track', methods=['POST'])
def track_engagement():
    """
    Receive and process engagement tracking data from webcam
    """
    try:
        from flask_jwt_extended import decode_token
        auth_header = request.headers.get('Authorization')
        user_id = "anonymous"
        
        if auth_header and "Bearer " in auth_header:
            try:
                user_id = get_jwt_identity()
            except: pass

        data = request.get_json()
        print(f">>> CV Frame Received from {data.get('user_id', user_id)}")
        
        frame_data = data.get('frame_data') or data.get('frame')
        if not frame_data:
            return jsonify({'error': 'Frame data is required'}), 400
        
        target_user = data.get('user_id') or user_id

        # Process engagement data using ML models
        engagement_result = process_engagement_data(
            frame_data=frame_data,
            screen_data=data.get('screen_data'),
            material_id=data.get('material_id')
        )
        
        # Save to database
        engagement_log = EngagementLog.create(
            user_id=user_id,
            material_id=data.get('material_id'),
            emotion=engagement_result['emotion'],
            emotion_conf=engagement_result['emotion_conf'],
            engagement_score=engagement_result['engagement_score'],
            engagement_state=engagement_result['engagement_state'],
            gaze=engagement_result['gaze'],
            posture=engagement_result['posture'],
            ocr_excerpt=engagement_result.get('ocr_excerpt'),
            context_match=engagement_result.get('context_match'),
            engagement_context_state=engagement_result.get('engagement_context_state')
        )

        # Fix 1: Sync to StudentEngagement collection
        try:
            from models import db
            db.StudentEngagement.insert_one({
                "user_id": user_id,
                "timestamp": engagement_log['timestamp'],
                "engagement_score": engagement_result['engagement_score'],
                "emotion": engagement_result['emotion'],
                "gaze": engagement_result['gaze'],
                "posture": engagement_result['posture'],
                "engagement_state": engagement_result['engagement_state'],
                "interaction_id": data.get('material_id'),
                "metadata": {
                    "emotion_conf": engagement_result['emotion_conf'],
                    "ocr_excerpt": engagement_result.get('ocr_excerpt'),
                    "context_match": engagement_result.get('context_match'),
                    "engagement_context_state": engagement_result.get('engagement_context_state')
                }
            })
        except Exception as e:
            print(f"[CV] StudentEngagement sync error: {e}")

        # Broadcast to Agentic AI Core (Live Telemetry Hub)
        try:
            import requests
            requests.post("http://localhost:8000/api/telemetry/cv", json={
                "user_id": target_user,
                "engagement_score": engagement_result['engagement_score'],
                "emotion": engagement_result['emotion'],
                "metadata": {"source": "cv_module_live"}
            }, timeout=0.5)
        except Exception as e:
            print(f"Telemetry Broadcast Error: {e}")
        
        # Return formatted response
        response = {
            'timestamp': engagement_log['timestamp'].isoformat(),
            'emotion': engagement_log['emotion'],
            'emotion_conf': engagement_log['emotion_conf'],
            'engagement_score': engagement_log['engagement_score'],
            'engagement_state': engagement_log['engagement_state'],
            'gaze': engagement_log['gaze'],
            'posture': engagement_log['posture'],
            'ocr_excerpt': engagement_log.get('ocr_excerpt'),
            'context_match': engagement_log.get('context_match'),
            'engagement_context_state': engagement_log.get('engagement_context_state')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engagement_bp.route('/logs', methods=['GET'])
@jwt_required()
def get_engagement_logs():
    """Get engagement logs for current user"""
    try:
        user_id = get_jwt_identity()
        
        # Optional query parameters
        material_id = request.args.get('material_id')
        limit = request.args.get('limit', default=100, type=int)
        
        if material_id:
            logs = EngagementLog.find_by_material(material_id)
        else:
            logs = EngagementLog.find_by_user(user_id, limit=limit)
        
        return jsonify({
            'logs': [EngagementLog.to_dict(log) for log in logs],
            'count': len(logs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@engagement_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_engagement_summary():
    """Get engagement summary statistics for current user"""
    try:
        user_id = get_jwt_identity()
        
        # Get all logs for the user
        logs = EngagementLog.find_by_user(user_id, limit=1000)
        
        if not logs:
            return jsonify({
                'message': 'No engagement data available',
                'summary': {}
            }), 200
        
        # Calculate statistics
        total_logs = len(logs)
        avg_engagement = sum(log.get('engagement_score', 0) for log in logs if log.get('engagement_score')) / total_logs if total_logs > 0 else 0
        
        # Emotion distribution
        emotions = {}
        for log in logs:
            emotion = log.get('emotion')
            if emotion:
                emotions[emotion] = emotions.get(emotion, 0) + 1
        
        # Engagement state distribution
        states = {}
        for log in logs:
            state = log.get('engagement_state')
            if state:
                states[state] = states.get(state, 0) + 1
        
        summary = {
            'total_logs': total_logs,
            'avg_engagement_score': round(avg_engagement, 2),
            'emotion_distribution': emotions,
            'engagement_state_distribution': states,
            'most_common_emotion': max(emotions, key=emotions.get) if emotions else None,
            'most_common_state': max(states, key=states.get) if states else None
        }
        
        return jsonify({'summary': summary}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

