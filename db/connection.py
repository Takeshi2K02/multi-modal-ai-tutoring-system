import os
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

import certifi

# Use the URI from the prompt as default, but allow env var override
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://admin:admin@cluster0.ngps8t9.mongodb.net/?appName=Cluster0")

def get_db_connection():
    """
    Establishes a connection to MongoDB.
    Returns the database object.
    """
    try:
        # Fix: SSL only for remote connections
        client_options = {"serverSelectionTimeoutMS": 5000}
        if "mongodb+srv" in MONGO_URI or "ssl=true" in MONGO_URI.lower():
            import certifi
            client_options["tlsCAFile"] = certifi.where()
            client_options["tls"] = True
        client = MongoClient(MONGO_URI, **client_options)
        # Verify connection
        client.admin.command('ping')
        # Project ID: 25-26J-130: Clean Logging - Suppress success ping
        logging.getLogger('pymongo').setLevel(logging.CRITICAL)
        return client.get_database("edusynth_db")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        # In a real app, we might raise e, but for this starter template / mock mode, 
        # we might want to handle it gracefully if using mocks only.
        return None

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
