import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Global DB connection for persistence efficiency
_client = None
_db = None

def _get_db():
    global _client, _db
    if _db is None:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_tutor_db')
        _client = MongoClient(mongo_uri)
        _db = _client.get_database()
    return _db

async def _emit_event(event, data):
    from server import sio
    try:
        await sio.emit(event, data)
    except Exception as e:
        print(f"Socket Emit Error: {e}")

async def push_cv_data(user_id: str, engagement_score: float, emotion: str, metadata: dict = None):
    """
    Called by the CV module every 1.5s to log engagement and emotion.
    """
    db = _get_db()
    log_entry = {
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "engagement_score": engagement_score,
        "emotion": emotion,
        "metadata": metadata or {}
    }
    db.StudentEngagement.insert_one(log_entry)
    
    # Emit for Admin Dashboard (Remove ObjectId for JSON serialization)
    if "_id" in log_entry:
        del log_entry["_id"]
    log_entry["timestamp"] = log_entry["timestamp"].isoformat()
    await _emit_event("cv_update", log_entry)

async def push_rl_strategy(user_id: str, action_id: int, confidence: float, reasoning: str = None):
    """
    Called by the RL engine to log the decided action and confidence.
    """
    db = _get_db()
    strategy_entry = {
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "action_id": action_id,
        "confidence": confidence,
        "reasoning": reasoning
    }
    db.PedagogicalStrategy.insert_one(strategy_entry)
    
    # Emit for Admin Dashboard (Remove ObjectId for JSON serialization)
    from agent_core.schemas import RL_ACTION_MAP
    if "_id" in strategy_entry:
        del strategy_entry["_id"]
    strategy_entry["timestamp"] = strategy_entry["timestamp"].isoformat()
    strategy_entry["policy_name"] = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown")
    await _emit_event("rl_update", strategy_entry)
