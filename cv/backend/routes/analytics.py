from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import EngagementLog, MaterialAccess, LearningQuery
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get comprehensive analytics dashboard for student"""
    try:
        user_id = get_jwt_identity()
        
        # Time range (default: last 7 days)
        days = request.args.get('days', default=7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        # Get engagement logs
        engagement_logs = EngagementLog.find_by_user(user_id, limit=1000)
        
        # Filter by date
        engagement_logs = [log for log in engagement_logs if log.get('timestamp', datetime.min) >= since]
        
        # Material access
        material_access = MaterialAccess.find_by_user(user_id)
        material_access = [acc for acc in material_access if acc.get('access_time', datetime.min) >= since]
        
        # Learning queries
        queries = LearningQuery.find_by_user(user_id)
        queries_count = len([q for q in queries if q.get('created_at', datetime.min) >= since])
        
        # Calculate metrics
        if engagement_logs:
            avg_engagement = sum(log.get('engagement_score', 0) for log in engagement_logs 
                               if log.get('engagement_score')) / len(engagement_logs) if len(engagement_logs) > 0 else 0
            
            # Emotion trends
            emotion_timeline = []
            for log in engagement_logs[-50:]:  # Last 50 logs
                emotion_timeline.append({
                    'timestamp': log.get('timestamp').isoformat() if log.get('timestamp') else None,
                    'emotion': log.get('emotion'),
                    'engagement_score': log.get('engagement_score')
                })
        else:
            avg_engagement = 0
            emotion_timeline = []
        
        # Learning topics accessed (simplified)
        topic_access = {}
        
        # Calculate hourly engagement pattern
        hourly_engagement = {}
        for log in engagement_logs:
            if log.get('timestamp'):
                hour = log['timestamp'].hour
                if hour not in hourly_engagement:
                    hourly_engagement[hour] = []
                hourly_engagement[hour].append(log.get('engagement_score', 0))
        
        hourly_avg = {
            hour: round(sum(scores) / len(scores), 2) if scores else 0
            for hour, scores in hourly_engagement.items()
        }
        
        dashboard = {
            'period_days': days,
            'total_queries': queries_count,
            'materials_accessed': len(material_access),
            'total_engagement_logs': len(engagement_logs),
            'avg_engagement_score': round(avg_engagement, 2),
            'hourly_engagement_pattern': hourly_avg,
            'emotion_timeline': emotion_timeline,
            'topic_access_distribution': topic_access,
            'learning_sessions': len(set(str(acc.get('material_id')) for acc in material_access if acc.get('material_id')))
        }
        
        return jsonify({'dashboard': dashboard}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/confidence-report', methods=['GET'])
@jwt_required()
def get_confidence_report():
    """Generate detailed confidence and engagement report"""
    try:
        user_id = get_jwt_identity()
        material_id = request.args.get('material_id')
        
        # Get engagement logs
        if material_id:
            logs = EngagementLog.find_by_material(material_id)
        else:
            logs = EngagementLog.find_by_user(user_id, limit=500)
        
        if not logs:
            return jsonify({
                'message': 'No engagement data available',
                'report': {}
            }), 200
        
        # Calculate confidence metrics
        engagement_states = {
            'engaged': 0,
            'moderately_engaged': 0,
            'disengaged': 0
        }
        
        emotions = {
            'positive': 0,  # happy, focused
            'neutral': 0,   # neutral
            'negative': 0   # confused, frustrated, bored
        }
        
        for log in logs:
            # Categorize engagement state
            state = log.get('engagement_state', '')
            if state in engagement_states:
                engagement_states[state] += 1
            
            # Categorize emotions
            emotion = log.get('emotion', '')
            if emotion in ['happy', 'focused', 'engaged']:
                emotions['positive'] += 1
            elif emotion in ['confused', 'frustrated', 'bored', 'tired']:
                emotions['negative'] += 1
            else:
                emotions['neutral'] += 1
        
        total_logs = len(logs)
        
        # Calculate confidence score (0-1)
        # Higher engagement and positive emotions = higher confidence
        confidence_score = (
            (engagement_states.get('engaged', 0) * 1.0 +
             engagement_states.get('moderately_engaged', 0) * 0.5) / total_logs * 0.5 +
            emotions['positive'] / total_logs * 0.3 +
            (1 - emotions['negative'] / total_logs) * 0.2
        )
        
        report = {
            'total_samples': total_logs,
            'confidence_score': round(confidence_score, 2),
            'confidence_percentage': round(confidence_score * 100, 1),
            'engagement_distribution': engagement_states,
            'emotion_distribution': emotions,
            'avg_emotion_confidence': round(
                sum(log.get('emotion_conf', 0) for log in logs if log.get('emotion_conf')) / total_logs, 2
            ) if total_logs > 0 else 0,
            'avg_engagement_score': round(
                sum(log.get('engagement_score', 0) for log in logs if log.get('engagement_score')) / total_logs, 2
            ) if total_logs > 0 else 0,
            'interpretation': get_confidence_interpretation(confidence_score)
        }
        
        return jsonify({'report': report}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_confidence_interpretation(score):
    """Provide human-readable interpretation of confidence score"""
    if score >= 0.8:
        return "Excellent - Student is highly engaged and confident with the material"
    elif score >= 0.6:
        return "Good - Student shows solid understanding with occasional challenges"
    elif score >= 0.4:
        return "Moderate - Student is learning but experiencing some difficulty"
    elif score >= 0.2:
        return "Low - Student appears to be struggling with the material"
    else:
        return "Very Low - Student is disengaged and may need intervention"

@analytics_bp.route('/learning-path', methods=['GET'])
@jwt_required()
def get_learning_path():
    """Track student's learning journey and topic progression"""
    try:
        user_id = get_jwt_identity()
        
        # Get all learning queries with materials
        queries = LearningQuery.find_by_user(user_id, limit=100)
        
        # Get material accesses
        accesses = MaterialAccess.find_by_user(user_id)
        
        learning_path = []
        for query in queries:
            learning_path.append({
                'timestamp': query.get('created_at').isoformat() if query.get('created_at') else None,
                'query': query.get('query_text'),
                'materials_suggested': len(query.get('suggested_materials', [])) if query.get('suggested_materials') else 0
            })
        
        material_performance = []
        for access in accesses:
            # Get engagement logs for this material
            material_id = access.get('material_id')
            if material_id:
                engagement_logs = EngagementLog.find_by_material(material_id)
                avg_engagement = sum(log.get('engagement_score', 0) for log in engagement_logs) / len(engagement_logs) if engagement_logs else None
            else:
                avg_engagement = None
            
            material_performance.append({
                'material_id': material_id,
                'access_time': access.get('access_time').isoformat() if access.get('access_time') else None,
                'duration_seconds': access.get('duration_seconds'),
                'avg_engagement': round(avg_engagement, 2) if avg_engagement else None
            })
        
        return jsonify({
            'learning_path': learning_path,
            'material_performance': material_performance
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
