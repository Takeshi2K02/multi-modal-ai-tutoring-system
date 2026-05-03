import os
from bson import ObjectId
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Configuration (Requirement 2: No Hardcoded Values)
PLAN_ID = os.getenv("PATCH_PLAN_ID")
COLLECTION_ID = os.getenv("PATCH_COLLECTION_ID")
MONGO_URI = os.getenv("MONGO_URI")

def patch():
    if not PLAN_ID or not COLLECTION_ID:
        print("❌ Error: PATCH_PLAN_ID or PATCH_COLLECTION_ID not found in environment.")
        print("Usage: PATCH_PLAN_ID=xxx PATCH_COLLECTION_ID=yyy python scratch/patch_plan_collection.py")
        return

    print(f"--- Patching Plan: {PLAN_ID} ---")
    try:
        client = MongoClient(MONGO_URI)
        # Scan both likely database names
        db_names = ["edusynth_db", "EduSynth"]
        
        found = False
        for db_name in db_names:
            db = client.get_database(db_name)
            res = db.learning_plans.update_one(
                {"_id": ObjectId(PLAN_ID)},
                {"$set": {
                    "system_metadata.collection_id": COLLECTION_ID,
                    "collection_id": COLLECTION_ID,
                    "system_metadata.vector_provider": "pinecone"
                }}
            )
            if res.matched_count > 0:
                print(f"✅ Success: Plan {PLAN_ID} updated in DB: {db_name}")
                found = True
                break
        
        if not found:
            print(f"❌ Error: Plan {PLAN_ID} not found in any standard collection.")

        # Sync Sessions
        for db_name in db_names:
            db = client.get_database(db_name)
            sess_res = db.learning_sessions.update_many(
                {"plan_id": ObjectId(PLAN_ID)},
                {"$set": {"collection_id": COLLECTION_ID}}
            )
            if sess_res.modified_count > 0:
                print(f"✅ Success: {sess_res.modified_count} sessions linked in DB: {db_name}")
        
    except Exception as e:
        print(f"❌ Patch failed: {e}")

if __name__ == "__main__":
    patch()
