import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_tutor_db')
    client = MongoClient(mongo_uri)
    db = client.get_database()

    print(f"Connecting to MongoDB at: {mongo_uri}")

    # 1. Create Collections
    collections = ['StudentEngagement', 'PedagogicalStrategy']
    for col in collections:
        if col not in db.list_collection_names():
            db.create_collection(col)
            print(f"Created collection: {col}")
        else:
            print(f"Collection {col} already exists.")

    # 2. Create Compound Indexes (user_id, timestamp)
    # Optimized for O(1) "Latest" lookup
    for col_name in collections:
        col = db[col_name]
        index_name = col.create_index([('user_id', 1), ('timestamp', -1)])
        print(f"Created compound index for {col_name}: {index_name}")

    # 3. Create TTL Index for StudentEngagement (24 hours)
    # 24 hours = 24 * 60 * 60 = 86400 seconds
    engagement_col = db['StudentEngagement']
    ttl_index_name = engagement_col.create_index(
        "timestamp", 
        expireAfterSeconds=86400
    )
    print(f"Created TTL index (24h) for StudentEngagement: {ttl_index_name}")

    print("\nDatabase setup complete.")

if __name__ == "__main__":
    setup_database()
