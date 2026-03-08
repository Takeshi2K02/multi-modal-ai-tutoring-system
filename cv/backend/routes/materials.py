from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import LearningQuery, Material, MaterialAccess
from services.openai_service import suggest_materials
import json

materials_bp = Blueprint('materials', __name__)

@materials_bp.route('/suggest', methods=['POST'])
@jwt_required()
def suggest_learning_materials():
    """Get AI-powered material suggestions based on student query"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'query' not in data:
            return jsonify({'error': 'Query text is required'}), 400
        
        query_text = data['query']
        
        # Get material suggestions from OpenAI
        suggestions = suggest_materials(query_text)
        
        # Save query and suggestions to database
        learning_query = LearningQuery.create(
            user_id=user_id,
            query_text=query_text,
            suggested_materials=suggestions
        )
        
        return jsonify({
            'query_id': str(learning_query['_id']),
            'query': query_text,
            'materials': suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@materials_bp.route('/access', methods=['POST'])
@jwt_required()
def log_material_access():
    """Log when a student accesses a material"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if 'material_id' not in data:
            return jsonify({'error': 'Material ID is required'}), 400
        
        # Check if material exists
        material = Material.find_by_id(data['material_id'])
        if not material:
            return jsonify({'error': 'Material not found'}), 404
        
        # Log access
        access = MaterialAccess.create(
            user_id=user_id,
            material_id=data['material_id'],
            query_id=data.get('query_id'),
            duration_seconds=data.get('duration_seconds')
        )
        
        return jsonify({
            'message': 'Access logged',
            'access': MaterialAccess.to_dict(access)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@materials_bp.route('/history', methods=['GET'])
@jwt_required()
def get_material_history():
    """Get student's material access history"""
    try:
        user_id = get_jwt_identity()
        
        # Get all queries and accessed materials
        queries = LearningQuery.find_by_user(user_id)
        accesses = MaterialAccess.find_by_user(user_id)
        
        return jsonify({
            'queries': [LearningQuery.to_dict(q) for q in queries],
            'accessed_materials': [MaterialAccess.to_dict(a) for a in accesses]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@materials_bp.route('/<material_id>', methods=['GET'])
@jwt_required()
def get_material(material_id):
    """Get specific material details"""
    try:
        material = Material.find_by_id(material_id)
        
        if not material:
            return jsonify({'error': 'Material not found'}), 404
        
        return jsonify({'material': Material.to_dict(material)}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@materials_bp.route('/create', methods=['POST'])
@jwt_required()
def create_material():
    """Create a new learning material (admin/teacher feature)"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'material_type', 'url']
        if not all(k in data for k in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        material = Material.create(
            title=data['title'],
            material_type=data['material_type'],
            url=data['url'],
            topic=data.get('topic'),
            description=data.get('description')
        )
        
        return jsonify({
            'message': 'Material created',
            'material': Material.to_dict(material)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

