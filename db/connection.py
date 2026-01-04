import os
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
        # tlsCAFile=certifi.where() fixes SSL certificate verify failed on Mac
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
        # Verify connection
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
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
