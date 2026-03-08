import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # MongoDB
    MONGO_URI = os.getenv(
        'MONGO_URI',
        'mongodb://localhost:27017/ai_tutor_db'
    )
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Model Paths
    ENGAGEMENT_MODEL_PATH = os.path.join('..', 'trained_models', 'engagement_model.pth')
    CONTENT_MODEL_PATH = os.path.join('..', 'trained_models', 'content_model.pth')
    
    # Upload folders
    UPLOAD_FOLDER = os.path.join('uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Engagement tracking
    ENGAGEMENT_LOG_INTERVAL = 2  # seconds
    MIN_CONFIDENCE_THRESHOLD = 0.5

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/ai_tutor_test_db'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
