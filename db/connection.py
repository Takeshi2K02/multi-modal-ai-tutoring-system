import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

import certifi

# Use the URI from env var, mandatory for production (Project ID: 25-26J-130)
MONGO_URI = os.getenv("MONGO_URI")

def get_db_connection():
    """
    Establishes a connection to MongoDB.
    Raises ConnectionError if the database is unreachable.
    """
    if not MONGO_URI:
        raise ConnectionError("MONGO_URI not found in environment variables. Please check your .env file.")

    try:
        # Fix: SSL only for remote connections
        client_options = {"serverSelectionTimeoutMS": 5000}
        if "mongodb+srv" in MONGO_URI or "ssl=true" in MONGO_URI.lower():
            client_options["tlsCAFile"] = certifi.where()
            client_options["tls"] = True
            
        client = MongoClient(MONGO_URI, **client_options)
        
        # Verify connection immediately
        client.admin.command('ping')
        
        # Suppress verbose pymongo logs
        logging.getLogger('pymongo').setLevel(logging.CRITICAL)
        
        # Resolve database name from URI if possible, or fallback to default
        db_name = MONGO_URI.split("/")[-1].split("?")[0] or "edusynth_db"
        return client.get_database(db_name)
        
    except Exception as e:
        # Crash Loudly (Requirement 1)
        error_msg = f"FATAL: Could not connect to MongoDB at {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else 'local'}. Error: {e}"
        print(f"\n{'!' * 60}\n{error_msg}\n{'!' * 60}\n")
        raise ConnectionError(error_msg)

def get_students_collection(db):
    if db is not None:
        return db["students"]
    return None

def get_interactions_collection(db):
    if db is not None:
        return db["interactions"]
    return None

def get_profiles_collection(db):
    if db is not None:
        return db["student_profiles"]
    return None

def get_users_collection(db):
    if db is not None:
        return db["users"]
    return None
