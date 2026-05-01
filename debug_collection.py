"""
Diagnostic script — Phase 2: Check learning_sessions collection.
"""
import os
import bson
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi

load_dotenv()

SESSION_ID = "69f49785dccb1b690ef18b87"
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://admin:admin@cluster0.ngps8t9.mongodb.net/?appName=Cluster0")

def get_db():
    opts = {"serverSelectionTimeoutMS": 8000}
    if "mongodb+srv" in MONGO_URI or "ssl=true" in MONGO_URI.lower():
        opts["tlsCAFile"] = certifi.where()
        opts["tls"] = True
    client = MongoClient(MONGO_URI, **opts)
    client.admin.command("ping")
    return client.get_database("edusynth_db")

def debug():
    db = get_db()
    print(f"✅ Collections: {db.list_collection_names()}\n")

    # --- Check learning_sessions collection ---
    print(f"[Step 1] Looking up session in 'learning_sessions' ...")
    session = db.learning_sessions.find_one({"_id": bson.ObjectId(SESSION_ID)})

    if not session:
        print(f"   ❌ Session {SESSION_ID} NOT found in 'learning_sessions'")
        # List most recent sessions so we know what actually exists
        recent = list(db.learning_sessions.find().sort("_id", -1).limit(5))
        print(f"\n   Last 5 sessions in learning_sessions:")
        for s in recent:
            print(f"     _id={s['_id']}  student_id={s.get('student_id')}  plan_id={s.get('plan_id')!r}")
        return

    print(f"   ✅ Session found. Keys: {list(session.keys())}")
    print(f"   student_id: {session.get('student_id')}")
    print(f"   plan_id raw: {session.get('plan_id')!r}")
    print(f"   plan_id type: {type(session.get('plan_id'))}")

    plan_id = session.get("plan_id")
    if not plan_id:
        print(f"\n❌ CASE B: No plan_id on session — run repair")
        return

    # --- Check learning_plans ---
    print(f"\n[Step 2] Looking up plan '{plan_id}' in 'learning_plans' ...")
    try:
        plan = db.learning_plans.find_one({"_id": bson.ObjectId(str(plan_id))})
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    if not plan:
        print(f"   ❌ Plan {plan_id} NOT found")
        recent_plans = list(db.learning_plans.find().sort("_id", -1).limit(5))
        print(f"\n   Last 5 plans:")
        for p in recent_plans:
            print(f"     _id={p['_id']}  collection_id={p.get('system_metadata', {}).get('collection_id')}")
        return

    print(f"   ✅ Plan found. Keys: {list(plan.keys())}")
    sys_meta = plan.get("system_metadata", {})
    nested_cid = sys_meta.get("collection_id") if isinstance(sys_meta, dict) else None
    top_cid = plan.get("collection_id")

    print(f"   system_metadata:               {sys_meta!r}")
    print(f"   system_metadata.collection_id: {nested_cid!r}")
    print(f"   top-level collection_id:       {top_cid!r}")

    resolved = nested_cid or top_cid
    if resolved:
        print(f"\n✅ RESOLUTION SUCCESSFUL: {resolved}")
        print(f"   The data is fine — check that server.py queries 'learning_sessions' not 'sessions'")
    else:
        print(f"\n❌ CASE C: Plan {plan['_id']} has no collection_id — run targeted repair")

if __name__ == "__main__":
    debug()
