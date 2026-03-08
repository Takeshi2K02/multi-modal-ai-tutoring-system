"""
Initialize MongoDB database with sample data
"""
from models import init_db, User, Material
from app import create_app, bcrypt
from datetime import datetime

def initialize_database():
    """Initialize database with sample data"""
    print("Initializing MongoDB database...")
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        # Initialize MongoDB connection
        db = init_db(app)
        
        print("Creating MongoDB database...")
        
        # Initialize MongoDB connection
        db = init_db(app)
        
        print("MongoDB connection established")
        
        # Clear existing data
        db.users.delete_many({})
        db.materials.delete_many({})
        db.learning_queries.delete_many({})
        db.material_access.delete_many({})
        db.engagement_logs.delete_many({})
        
        print("Cleared existing data")
        
        # Create sample users
        users_data = [
            {'username': 'student1', 'email': 'student1@example.com', 'password': 'password123'},
            {'username': 'student2', 'email': 'student2@example.com', 'password': 'password123'},
            {'username': 'john_doe', 'email': 'john@example.com', 'password': 'password123'}
        ]
        
        created_users = []
        for user_info in users_data:
            password_hash = bcrypt.generate_password_hash(user_info['password']).decode('utf-8')
            user = User.create(
                username=user_info['username'],
                email=user_info['email'],
                password_hash=password_hash
            )
            created_users.append(user)
            print(f"Created user: {user_info['username']}")
        
        # Create sample materials
        materials_data = [
            {
                'title': 'Introduction to Python Programming',
                'material_type': 'video',
                'url': 'https://www.youtube.com/watch?v=example1',
                'topic': 'python',
                'description': 'Complete Python tutorial for beginners'
            },
            {
                'title': 'Machine Learning Fundamentals',
                'material_type': 'pdf',
                'url': 'https://example.com/ml-fundamentals.pdf',
                'topic': 'machine-learning',
                'description': 'Comprehensive guide to ML basics'
            },
            {
                'title': 'Data Structures and Algorithms',
                'material_type': 'blog',
                'url': 'https://example.com/blog/dsa',
                'topic': 'algorithms',
                'description': 'Essential DSA concepts explained'
            },
            {
                'title': 'Web Development with React',
                'material_type': 'video',
                'url': 'https://www.youtube.com/watch?v=example2',
                'topic': 'web-development',
                'description': 'Modern React development course'
            },
            {
                'title': 'Database Design Principles',
                'material_type': 'pdf',
                'url': 'https://example.com/db-design.pdf',
                'topic': 'databases',
                'description': 'Learn database design best practices'
            },
            {
                'title': 'Calculus I - Derivatives',
                'material_type': 'video',
                'url': 'https://www.youtube.com/watch?v=example3',
                'topic': 'mathematics',
                'description': 'Understanding derivatives and their applications'
            },
            {
                'title': 'Physics - Newton\'s Laws',
                'material_type': 'blog',
                'url': 'https://example.com/blog/newtons-laws',
                'topic': 'physics',
                'description': 'Detailed explanation of Newton\'s three laws'
            },
            {
                'title': 'English Grammar Essentials',
                'material_type': 'pdf',
                'url': 'https://example.com/grammar.pdf',
                'topic': 'english',
                'description': 'Master essential grammar rules'
            }
        ]
        
        created_materials = []
        for material_info in materials_data:
            material = Material.create(**material_info)
            created_materials.append(material)
            print(f"Created material: {material_info['title']}")
        
        print("\n" + "="*60)
        print("DATABASE INITIALIZATION COMPLETE!")
        print("="*60)
        print(f"\nCreated {len(created_users)} users")
        print(f"Created {len(created_materials)} materials")
        print("\nSample login credentials:")
        print("-" * 60)
        for user_info in users_data:
            print(f"Email: {user_info['email']:30s} Password: {user_info['password']}")
        print("-" * 60)
        print("\nYou can now start the backend server with: python app.py")
        print("="*60)

if __name__ == '__main__':
    initialize_database()
