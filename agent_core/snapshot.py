import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from agent_core.schemas import StudentStateSnapshot, RL_ACTION_MAP

# Global DB connection for efficiency
_client = None
_db = None

def _get_db():
    global _client, _db
    if _db is None:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_tutor_db')
        _client = MongoClient(mongo_uri)
        _db = _client.get_database()
    return _db

def get_student_snapshot(user_id: str) -> StudentStateSnapshot:
    """
    Performs a non-blocking find_one (sort by latest) for both CV and RL data.
    Calculates engagement trends and deviations.
    """
    db = _get_db()

    # 1. Fetch Latest CV Data
    latest_cv = db.StudentEngagement.find_one(
        {"user_id": user_id}, 
        sort=[("timestamp", -1)]
    )

    # 2. Fetch Latest Performance Data
    latest_perf = db.Performance.find_one(
        {"user_id": user_id},
        sort=[("timestamp", -1)]
    )
    
    # 3. Fetch Latest RL Strategy
    latest_rl = db.PedagogicalStrategy.find_one(
        {"user_id": user_id}, 
        sort=[("timestamp", -1)]
    )

    # --- Cold Start Logic ---
    if not latest_cv:
        # print(f"Cold Start: No history for student {user_id}. Using defaults.")
        return StudentStateSnapshot(
            engagement_trend="stable",
            current_affect={"emotion": "neutral", "score": 0.5},
            rl_strategy="Diagnostic Mode - Baseline Curriculum",
            performance_summary="New student. Initial calibration needed.",
            deviation_alert=False
        )

    # 4. Calculate Historical Average & Trend (last 10m)
    ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
    recent_logs = list(db.StudentEngagement.find({
        "user_id": user_id,
        "timestamp": {"$gte": ten_min_ago}
    }).sort("timestamp", -1))

    # Engagement Trend
    trend = "stable"
    if len(recent_logs) >= 2:
        diff = recent_logs[0]["engagement_score"] - recent_logs[-1]["engagement_score"]
        if diff > 0.15: trend = "improving"
        elif diff < -0.15: trend = "declining"

    # Historical Average for Deviation Detection
    if recent_logs:
        hist_avg = sum(l["engagement_score"] for l in recent_logs) / len(recent_logs)
    else:
        hist_avg = 0.5 # Fallback

    # Deviation Alert (current < 50% of historical average)
    current_score = latest_cv.get("engagement_score", 0.5)
    deviation_alert = current_score < (hist_avg * 0.5)

    # 5. Map Action ID to Policy Name
    action_id = latest_rl.get("action_id", 0) if latest_rl else 0
    strategy_name = RL_ACTION_MAP.get(action_id, {}).get("name", "General Instruction")

    perf_summary = "Real-time monitoring active."
    if latest_perf:
        perf_summary = f"Accuracy: {latest_perf.get('accuracy', 0)*100:.0f}%, Difficulty: {latest_perf.get('difficulty', 0):.2f}"

    return StudentStateSnapshot(
        engagement_trend=trend,
        current_affect={
            "emotion": latest_cv.get("emotion", "neutral"),
            "score": current_score
        },
        rl_strategy=strategy_name,
        action_id=action_id, # Hard constraint for pruning
        performance_summary=perf_summary,
        deviation_alert=deviation_alert,
        mastery_level=latest_perf.get("mastery", 0.5) if latest_perf else 0.5,
        session_fatigue=0.0, # Placeholder or calc derived from time_on_task
        confidence=latest_cv.get("emotion_conf", 0.5)
    )
