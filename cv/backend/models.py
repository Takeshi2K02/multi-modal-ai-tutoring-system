from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os

# MongoDB connection
mongo_client = None
db = None

def init_db(app):
    """Initialize MongoDB connection"""
    global mongo_client, db
    mongo_uri = app.config['MONGO_URI']
    
    # Connect to MongoDB
    mongo_client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,   # fail fast if Atlas unreachable
        connectTimeoutMS=5000,
        socketTimeoutMS=20000,
    )
    
    # Extract database name from URI or use default
    if '/' in mongo_uri and '?' in mongo_uri:
        # Format: mongodb://.../{dbname}?options
        uri_parts = mongo_uri.split('?')[0]  # Remove query params
        db_name = uri_parts.split('/')[-1]  # Get last part after /
    elif '/' in mongo_uri:
        db_name = mongo_uri.split('/')[-1]
    else:
        db_name = 'ai_tutor_db'
    
    db = mongo_client[db_name]
    
    # Create indexes (skipped if DB is temporarily unreachable)
    try:
        db.users.create_index('email', unique=True)
        db.users.create_index('username', unique=True)
        db.materials.create_index('topic')
        db.engagement_logs.create_index([('user_id', 1), ('timestamp', -1)])
    except Exception as e:
        print(f"⚠️  MongoDB index creation skipped (DB may be unreachable): {e}")
    
    return db

class User:
    """User model for student authentication"""
    collection = 'users'
    
    @staticmethod
    def create(username, email, password_hash):
        user_data = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created_at': datetime.now()
        }
        result = db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return user_data
    
    @staticmethod
    def find_by_email(email):
        return db.users.find_one({'email': email})
    
    @staticmethod
    def find_by_username(username):
        return db.users.find_one({'username': username})
    
    @staticmethod
    def find_by_id(user_id):
        return db.users.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def to_dict(user_data):
        if not user_data:
            return None
        return {
            'id': str(user_data['_id']),
            'username': user_data['username'],
            'email': user_data['email'],
            'created_at': user_data['created_at'].isoformat()
        }

class LearningQuery:
    """Store student learning queries and suggested materials"""
    collection = 'learning_queries'
    
    @staticmethod
    def create(user_id, query_text, suggested_materials=None):
        query_data = {
            'user_id': user_id,
            'query_text': query_text,
            'suggested_materials': suggested_materials or [],
            'created_at': datetime.now()
        }
        result = db.learning_queries.insert_one(query_data)
        query_data['_id'] = result.inserted_id
        return query_data
    
    @staticmethod
    def find_by_user(user_id, limit=10):
        return list(db.learning_queries.find({'user_id': user_id}).sort('created_at', -1).limit(limit))
    
    @staticmethod
    def to_dict(query_data):
        if not query_data:
            return None
        return {
            'id': str(query_data['_id']),
            'user_id': query_data['user_id'],
            'query_text': query_data['query_text'],
            'suggested_materials': query_data.get('suggested_materials', []),
            'created_at': query_data['created_at'].isoformat()
        }

class Material:
    """Learning materials (PDFs, blogs, videos)"""
    collection = 'materials'
    
    @staticmethod
    def create(title, material_type, url, topic=None, description=None):
        material_data = {
            'title': title,
            'material_type': material_type,
            'url': url,
            'topic': topic,
            'description': description,
            'created_at': datetime.now()
        }
        result = db.materials.insert_one(material_data)
        material_data['_id'] = result.inserted_id
        return material_data
    
    @staticmethod
    def find_by_id(material_id):
        return db.materials.find_one({'_id': ObjectId(material_id)})
    
    @staticmethod
    def find_by_topic(topic):
        return list(db.materials.find({'topic': topic}))
    
    @staticmethod
    def to_dict(material_data):
        if not material_data:
            return None
        return {
            'id': str(material_data['_id']),
            'title': material_data['title'],
            'material_type': material_data['material_type'],
            'url': material_data['url'],
            'topic': material_data.get('topic'),
            'description': material_data.get('description'),
            'created_at': material_data['created_at'].isoformat()
        }

class MaterialAccess:
    """Track which materials students access"""
    collection = 'material_access'
    
    @staticmethod
    def create(user_id, material_id, query_id=None, duration_seconds=None):
        access_data = {
            'user_id': user_id,
            'material_id': material_id,
            'query_id': query_id,
            'access_time': datetime.now(),
            'duration_seconds': duration_seconds
        }
        result = db.material_access.insert_one(access_data)
        access_data['_id'] = result.inserted_id
        return access_data
    
    @staticmethod
    def find_by_user(user_id):
        return list(db.material_access.find({'user_id': user_id}).sort('access_time', -1))
    
    @staticmethod
    def to_dict(access_data):
        if not access_data:
            return None
        return {
            'id': str(access_data['_id']),
            'user_id': access_data['user_id'],
            'material_id': access_data['material_id'],
            'query_id': access_data.get('query_id'),
            'access_time': access_data['access_time'].isoformat(),
            'duration_seconds': access_data.get('duration_seconds')
        }

class EngagementLog:
    """Store real-time engagement tracking data"""
    collection = 'engagement_logs'
    
    @staticmethod
    def create(user_id, material_id=None, emotion=None, emotion_conf=None, engagement_score=None,
               engagement_state=None, gaze=None, posture=None, ocr_excerpt=None, context_match=None,
               engagement_context_state=None):
        log_data = {
            'user_id': user_id,
            'material_id': material_id,
            'timestamp': datetime.now(),
            'emotion': emotion,
            'emotion_conf': emotion_conf,
            'engagement_score': engagement_score,
            'engagement_state': engagement_state,
            'gaze': gaze,
            'posture': posture,
            'ocr_excerpt': ocr_excerpt,
            'context_match': context_match,
            'engagement_context_state': engagement_context_state
        }
        result = db.engagement_logs.insert_one(log_data)
        log_data['_id'] = result.inserted_id
        return log_data
    
    @staticmethod
    def find_by_user(user_id, limit=100):
        return list(db.engagement_logs.find({'user_id': user_id}).sort('timestamp', -1).limit(limit))
    
    @staticmethod
    def find_by_material(material_id):
        return list(db.engagement_logs.find({'material_id': material_id}).sort('timestamp', -1))
    
    @staticmethod
    def get_user_stats(user_id):
        """Get aggregated engagement statistics for a user"""
        pipeline = [
            {'$match': {'user_id': user_id}},
            {'$group': {
                '_id': None,
                'avg_engagement': {'$avg': '$engagement_score'},
                'total_sessions': {'$sum': 1},
                'emotions': {'$push': '$emotion'}
            }}
        ]
        result = list(db.engagement_logs.aggregate(pipeline))
        return result[0] if result else None
    
    @staticmethod
    def to_dict(log_data):
        if not log_data:
            return None
        return {
            'id': str(log_data['_id']),
            'user_id': log_data['user_id'],
            'material_id': log_data.get('material_id'),
            'timestamp': log_data['timestamp'].isoformat(),
            'emotion': log_data.get('emotion'),
            'emotion_conf': log_data.get('emotion_conf'),
            'engagement_score': log_data.get('engagement_score'),
            'engagement_state': log_data.get('engagement_state'),
            'gaze': log_data.get('gaze'),
            'posture': log_data.get('posture'),
            'ocr_excerpt': log_data.get('ocr_excerpt'),
            'context_match': log_data.get('context_match'),
            'engagement_context_state': log_data.get('engagement_context_state')
        }

