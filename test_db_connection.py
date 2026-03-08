import os
from pymongo import MongoClient
import certifi

# URI found in cv/backend/.env
MONGO_URI = "mongodb+srv://Dileka_21:Dileka123@cluster0.g3llspy.mongodb.net/ai_tutor_db?appName=Cluster0"

def test_connection():
    try:
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        
        # Check databases
        db_names = client.list_database_names()
        print(f"Databases: {db_names}")
        
        # Check elearning
        db = client.get_database("elearning")
        print(f"Collections in 'elearning': {db.list_collection_names()}")
        
        # Check for sessions
        sessions_col = db.get_collection("learning_sessions")
        count = sessions_col.count_documents({})
        print(f"Total sessions in 'learning_sessions': {count}")
        
        # Check for plans
        plans_col = db.get_collection("learning_plans")
        print(f"Total plans in 'learning_plans': {plans_col.count_documents({})}")
        
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_connection()
