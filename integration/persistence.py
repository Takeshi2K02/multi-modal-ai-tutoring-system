import os
import time
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Project ID: 25-26J-130: Throttling Trackers
_last_cv_print_time = 0
_last_cv_state = {"emotion": None, "score": 0}
_last_rl_print_time = 0
_last_rl_action = None

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

async def push_cv_data(user_id: str, engagement_score: float, emotion: str, 
                       gaze: str = "unknown", posture: str = "unknown", 
                       engagement_state: str = "unknown", interaction_id: str = None,
                       metadata: dict = None):
    """
    Called by the CV module every 1.5s to log engagement and emotion.
    """
    db = _get_db()
    log_entry = {
        "user_id": user_id,
        "timestamp": datetime.utcnow(),
        "engagement_score": engagement_score,
        "emotion": emotion,
        "gaze": gaze,
        "posture": posture,
        "engagement_state": engagement_state,
        "interaction_id": interaction_id,
        "metadata": metadata or {}
    }
    db.StudentEngagement.insert_one(log_entry)
    
    # Project ID: 25-26J-130: Clean Logging & Throttling
    global _last_cv_print_time, _last_cv_state
    now = time.time()
    state_changed = (emotion != _last_cv_state["emotion"]) or (abs(engagement_score - _last_cv_state["score"]) > 0.3)
    heartbeat = (now - _last_cv_print_time) >= 30

    if state_changed or heartbeat:
        print(f"[CV] Engagement: {engagement_score:.2f} | Emotion: {emotion} {'(State Change)' if state_changed and not heartbeat else '(Heartbeat)'}")
        _last_cv_print_time = now
        _last_cv_state = {"emotion": emotion, "score": engagement_score}
    
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
    
    # Project ID: 25-26J-130: Clean Logging & Throttling
    global _last_rl_print_time, _last_rl_action
    now = time.time()
    state_changed = (action_id != _last_rl_action)
    heartbeat = (now - _last_rl_print_time) >= 30

    if state_changed or heartbeat:
        from agent_core.schemas import RL_ACTION_MAP
        action_name = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown")
        print(f"[RL] Selected Action: {action_id} ({action_name}) | Conf: {confidence:.2f} {'(State Change)' if state_changed and not heartbeat else '(Heartbeat)'}")
        _last_rl_print_time = now
        _last_rl_action = action_id
    
    # Emit for Admin Dashboard (Remove ObjectId for JSON serialization)
    from agent_core.schemas import RL_ACTION_MAP
    if "_id" in strategy_entry:
        del strategy_entry["_id"]
    strategy_entry["timestamp"] = strategy_entry["timestamp"].isoformat()
    strategy_entry["policy_name"] = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown")
    await _emit_event("rl_update", strategy_entry)
