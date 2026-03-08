from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from config import config
from models import init_db
import os

# Initialize extensions
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # Initialize MongoDB (non-fatal — server starts even if Atlas is unreachable)
    try:
        init_db(app)
        print("✅ MongoDB connected")
    except Exception as e:
        print(f"⚠️  MongoDB unavailable, continuing without DB: {e}")
    
    # Create upload folders
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.materials import materials_bp
    from routes.engagement import engagement_bp
    from routes.analytics import analytics_bp
    from routes.content import content_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(materials_bp, url_prefix='/api/materials')
    app.register_blueprint(engagement_bp, url_prefix='/api/engagement')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(content_bp, url_prefix='/api/content')
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'EduSynth is running'}), 200
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5000, debug=True)
