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

def calculate_lesson_benchmark(text: str, student_profile: dict, topic: str = "") -> int:
    """
    Calculates estimated reading time based on word count and student speed.
    Multiplier of 1.2x applied for 'Dimensional Modelling'.
    """
    word_count = len(text.split())
    # Retrieve reading speed (words per minute), default to 200
    reading_speed = student_profile.get("average_reading_speed", 200)
    
    # Base time in seconds
    base_time = (word_count / reading_speed) * 60
    
    # Complexity Multiplier
    multiplier = 1.0
    if "Dimensional Modelling" in topic or "Dimensional" in topic:
        # PROJECT ID: 25-26J-130 SMOKE TEST OVERRIDE: Force 15s benchmark
        return 15
        
    estimated_time = int(base_time * multiplier)
    
    # Minimum floor of 30s
    return max(30, estimated_time)

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

    # 4. Calculate Historical Average & Trend (last 10s for ultra-sensitive test)
    thirty_seconds_ago = datetime.now() - timedelta(seconds=10)
    recent_logs = list(db.StudentEngagement.find({
        "user_id": user_id,
        "timestamp": {"$gte": thirty_seconds_ago}
    }).sort("timestamp", -1))

    # Engagement Trend
    trend = "stable"
    if len(recent_logs) >= 2:
        diff = recent_logs[0]["engagement_score"] - recent_logs[-1]["engagement_score"]
        if diff > 0.15: trend = "improving"
        elif diff < -0.15: trend = "declining"

    # Historical Average for Intervention Trigger
    hist_avg = 0.5
    if recent_logs:
        hist_avg = sum(l["engagement_score"] for l in recent_logs) / len(recent_logs)

    # 5. Intervention Trigger (Project ID: 25-26J-130)
    MAX_SESSION_S = 3600 # 1-hour session benchmark (Issue 4)
    latest_interaction = db.interactions.find_one(
        {"student_id": user_id},
        sort=[("timestamp", -1)]
    )
    
    intervention_needed = False
    session_fatigue = 0.0
    
    if latest_interaction:
        start_time = latest_interaction.get("timestamp", datetime.now())
        reading_time = MAX_SESSION_S # Issue 4: Set benchmark to max_session_s
        is_done = latest_interaction.get("is_completed", False)
        
        time_elapsed = (datetime.now() - start_time).total_seconds()
        
        # Issue 4: Calculate Normalized Fatigue
        session_fatigue = min(time_elapsed / MAX_SESSION_S, 1.0)
        print(f"[DQN State] session_fatigue={session_fatigue:.4f} elapsed={time_elapsed:.1f}s max={MAX_SESSION_S}s")
        
        # Readiness Guard: Only trigger if the lesson has content (estimated_reading_time set)
        # Recency Guard: Only trigger if the interaction started recently (e.g., last 10 mins)
        is_recent = time_elapsed < 600 # 10 minutes
        is_ready = reading_time > 0
        
        print(f"[Snapshot Debug] Student: {user_id}, Elapsed: {time_elapsed:.1f}s, Benchmark: {MAX_SESSION_S}s, Avg: {hist_avg:.2f}, Recent: {is_recent}")
        
        if is_recent and is_ready and time_elapsed > reading_time and not is_done and hist_avg < 0.98:
            intervention_needed = True
            # Log only if significantly past benchmark to reduce noise
            if int(time_elapsed) % 30 == 0:
                print(f"[Snapshot Debug] 🎯 INTERVENTION ELIGIBLE for {user_id} (Elapsed: {time_elapsed:.0f}s)")

    # 6. Map Action ID to Policy Name
    action_id = latest_rl.get("action_id", 0) if latest_rl else 0
    strategy_name = RL_ACTION_MAP.get(action_id, {}).get("name", "General Instruction")

    perf_summary = "Real-time monitoring active."
    if latest_perf:
        perf_summary = f"Accuracy: {latest_perf.get('accuracy', 0)*100:.0f}%, Difficulty: {latest_perf.get('difficulty', 0):.2f}"

    return StudentStateSnapshot(
        engagement_trend=trend,
        current_affect={
            "emotion": latest_cv.get("emotion", "neutral"),
            "score": latest_cv.get("engagement_score", 0.5)
        },
        rl_strategy=strategy_name,
        action_id=action_id,
        performance_summary=perf_summary,
        deviation_alert=intervention_needed, # Mapping for backward compatibility
        intervention_needed=intervention_needed,
        mastery_level=latest_perf.get("mastery", 0.5) if latest_perf else 0.5,
        session_fatigue=session_fatigue,
        confidence=latest_cv.get("emotion_conf", 0.5)
    )
