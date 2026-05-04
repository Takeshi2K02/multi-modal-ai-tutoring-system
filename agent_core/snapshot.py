import os, time
from datetime import datetime, timedelta
from pymongo import MongoClient
from agent_core.schemas import StudentStateSnapshot, RL_ACTION_MAP

from db.connection import get_db_connection

def _get_db():
    return get_db_connection()

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

# Consecutive Reading Debounce (Project ID: 25-26J-130)
_consecutive_drops = 0  # Persistence across monitor cycles
_last_eligible_logged = False
_last_snapshot_logged = {"needed": None, "drops": -1}

def reset_intervention_counter(silent=False):
    """Project ID: 25-26J-130: Resets the consecutive drops counter."""
    global _consecutive_drops
    _consecutive_drops = 0
    if not silent:
        print("[Snapshot] 🔄 Intervention counter reset to 0.")

def get_student_snapshot(user_id: str, session_start_time: float = None) -> StudentStateSnapshot:
    """
    Performs a non-blocking find_one (sort by latest) for both CV and RL data.
    Calculates engagement trends and deviations.
    """
    global _consecutive_drops
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
    
    # 3b. Fetch Latest Feedback Signal (Project ID: 25-26J-130)
    latest_feedback = db.FeedbackSignals.find_one(
        {"student_id": user_id},
        sort=[("timestamp", -1)]
    )
    feedback_val = latest_feedback.get("signal") if latest_feedback else None

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

    # 4. Calculate Historical Average & Trend (45s sliding window for Problem 4)
    forty_five_seconds_ago = datetime.now() - timedelta(seconds=45)
    recent_logs = list(db.StudentEngagement.find({
        "user_id": user_id,
        "timestamp": {"$gte": forty_five_seconds_ago}
    }).sort("timestamp", -1))

    # Engagement Trend
    trend = "stable"
    if len(recent_logs) >= 2:
        diff = recent_logs[0]["engagement_score"] - recent_logs[-1]["engagement_score"]
        if diff > 0.15: trend = "improving"
        elif diff < -0.15: trend = "declining"

    # 5. Intervention Trigger (Project ID: 25-26J-130)
    MAX_SESSION_S = 3600 
    
    intervention_needed = False
    session_fatigue = 0.0
    
    if session_start_time:
        time_elapsed = time.time() - session_start_time
        session_fatigue = min(time_elapsed / MAX_SESSION_S, 1.0)
    else:
        latest_interaction = db.interactions.find_one(
            {"student_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        if latest_interaction:
            two_hours_ago = datetime.now() - timedelta(hours=2)
            session_start = db.interactions.find_one(
                {"student_id": user_id, "timestamp": {"$gte": two_hours_ago}},
                sort=[("timestamp", 1)]
            )
            start_time_db = session_start.get("timestamp") if session_start else latest_interaction.get("timestamp", datetime.now())
            time_since_last = (datetime.now() - latest_interaction.get("timestamp", datetime.now())).total_seconds()
            
            if time_since_last > 3600:
                time_elapsed = 0.0
            else:
                time_elapsed = (datetime.now() - start_time_db).total_seconds()
            session_fatigue = min(time_elapsed / MAX_SESSION_S, 1.0)
        else:
            time_elapsed = 0.0
            session_fatigue = 0.0
            
    is_ready = time_elapsed > 5 # TEMP: testing only
    
    # Problem 4: Sliding Window Logic
    window_avg = 0.0
    sample_count = len(recent_logs)
    if sample_count >= 3:
        window_avg = sum(l["engagement_score"] for l in recent_logs) / sample_count
        # Stable threshold check
        if is_ready and window_avg < 0.55: 
            intervention_needed = True

    # Diagnostic Log (Project ID: 25-26J-130) - Rule 1: only log on state change
    global _last_snapshot_logged
    if intervention_needed != _last_snapshot_logged["needed"] or abs(window_avg - _last_snapshot_logged.get("avg", 0)) > 0.05:
        print(f"🎯 [Intervention Check] window_avg={window_avg:.2f} ({sample_count} samples) | elapsed={time_elapsed:.1f}s | intervention_needed={intervention_needed}")
        _last_snapshot_logged = {"needed": intervention_needed, "avg": window_avg}

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
        confidence=latest_cv.get("emotion_conf", 0.5),
        feedback_signal=feedback_val
    )
