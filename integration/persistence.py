import os
import time
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from agent_core.pedagogical_agent import PedagogicalAgent

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
    # print(f"[Pipeline] 👁️ CV Sensor Agent: Received telemetry for {user_id}")
    db = _get_db()
    log_entry = {
        "user_id": user_id,
        "timestamp": datetime.now(),
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
    # Project ID: 25-26J-130: State-Change Only Logging (Throttle: 10s)
    global _last_cv_print_time, _last_cv_state
    now = time.time()
    state_changed = (emotion != _last_cv_state["emotion"]) or (abs(engagement_score - _last_cv_state["score"]) > 0.3)
    throttle_expired = (now - _last_cv_print_time) >= 10

    if state_changed and throttle_expired:
        print(f"[CV] Engagement: {engagement_score:.2f} | Emotion: {emotion}")
        _last_cv_print_time = now
        _last_cv_state = {"emotion": emotion, "score": engagement_score}
    
    # Emit for Admin Dashboard (Remove ObjectId for JSON serialization)
    if "_id" in log_entry:
        del log_entry["_id"]
    log_entry["timestamp"] = log_entry["timestamp"].isoformat()
    await _emit_event("cv_update", log_entry)
    
    # --- RL BRIDGE: Trigger Policy Inference on Heartbeat (Project ID: 25-26J-130) ---
    try:
        from core.state import is_tot_running, active_student_synthesis
        if is_tot_running or user_id in active_student_synthesis:
            return
            
        # 1. Fetch Student Profile & Feedback Signal (Project ID: 25-26J-130)
        profile = db.student_profiles.find_one({"student_id": user_id}) or {}
        latest_feedback = db.FeedbackSignals.find_one({"student_id": user_id}, sort=[("timestamp", -1)])
        feedback_val = latest_feedback.get("signal") if latest_feedback else None
        
        # 2. Run Inference
        agent = PedagogicalAgent(user_id)
        # print(f"[Pipeline] 🧠 DQN Inference: Polling for optimal strategy for student state...")
        distribution = agent.get_action_distribution(engagement_score, emotion, profile, feedback_signal=feedback_val)
        decision = agent.select_action(distribution)
        
        # Project ID: 25-26J-130: Signal-Only DQN Logging
        if decision['policy_name'] != "Maintain Current Content":
            f_info = f" | fdbk={feedback_val}" if feedback_val is not None else ""
            print(f"[DQN] State: eng={engagement_score:.2f}, emo={emotion}{f_info} | Action: {decision['policy_name']} (Conf: {decision['confidence']:.2f})")
        
        # 3. Emit Policy Update for Live Monitor
        await _emit_event("policy_update", {
            "user_id": user_id,
            "distribution": distribution,
            "selected_action": decision,
            "timestamp": datetime.now().isoformat()
        })
        
        # 4. Reward Calculation Log
        # print(f"[RL Engine] --- Input Engagement: {engagement_score:.2f} | Selected Strategy: {decision['policy_name']} | Confidence: {int(decision['confidence']*100)}% ---")
        
        # 5. Persist the Strategy Decision
        await push_rl_strategy(user_id, decision["action_id"], decision["confidence"], decision["reasoning"])
        
    except Exception as e:
        print(f"RL Bridge Error: {e}")

async def push_rl_strategy(user_id: str, action_id: int, confidence: float, reasoning: str = None):
    """
    Called by the RL engine to log the decided action and confidence.
    """
    db = _get_db()
    strategy_entry = {
        "user_id": user_id,
        "timestamp": datetime.now(),
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
        # Internal persistence log suppressed; primary DQN log handled in push_cv_data bridge
        _last_rl_print_time = now
        _last_rl_action = action_id
    
    # Emit for Admin Dashboard (Remove ObjectId for JSON serialization)
    from agent_core.schemas import RL_ACTION_MAP
    if "_id" in strategy_entry:
        del strategy_entry["_id"]
    strategy_entry["timestamp"] = strategy_entry["timestamp"].isoformat()
    strategy_entry["policy_name"] = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown")
    await _emit_event("rl_update", strategy_entry)
