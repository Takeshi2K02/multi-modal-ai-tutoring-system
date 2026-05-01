import os
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables (same as server.py)
load_dotenv()

def repair():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("❌ MONGO_URI not found in environment")
        return

    client = MongoClient(mongo_uri)
    db = client.get_database()
    
    plan_id = "69f49784dccb1b690ef18b85"
    collection_id = "362aad49-6c75-4d60-adc5-40bfd4701797"
    
    print(f"Connecting to MongoDB...")
    
    result = db.learning_plans.update_one(
        { "_id": ObjectId(plan_id) },
        { "$set": { "system_metadata.collection_id": collection_id } }
    )
    
    if result.matched_count > 0:
        print(f"✅ Repaired plan {plan_id} → collection_id set to {collection_id}")
    else:
        print(f"⚠️ Plan {plan_id} not found in database.")

if __name__ == "__main__":
    repair()
