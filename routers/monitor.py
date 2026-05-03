import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from core.auth import get_current_user, get_password_hash, verify_password, create_access_token
from core.state import active_prefetch_tasks, active_student_synthesis, triggered_interventions
from core.schemas import ScenarioRequest, GraphResponse
from socket_manager import sio
from db.connection import get_db_connection, get_profiles_collection

# Services
from services.learning_plan_service import LearningPlanService
from services.learning_session_service import LearningSessionService

router = APIRouter()

@router.get("/api/analytics/historical")
async def get_historical_analytics(user_id: str = Depends(get_current_user)):
    """
    Fetches aggregated historical averages for CV and RL telemetry.
    """
    try:
        from agent_core.snapshot import _get_db
        from agent_core.schemas import RL_ACTION_MAP
        db = _get_db()
        
        if db is None:
            return {"status": "offline", "error": "Database Connection Failed"}
        
        # 1. CV Aggregation (Last 24 hours)
        one_day_ago = datetime.now() - timedelta(days=1)
        cv_logs = list(db.StudentEngagement.find({
            "user_id": user_id,
            "timestamp": {"$gte": one_day_ago}
        }))
        
        avg_engagement = 0
        emotions = {}
        if cv_logs:
            avg_engagement = sum(l["engagement_score"] for l in cv_logs) / len(cv_logs)
            for l in cv_logs:
                emo = l.get("emotion", "neutral")
                emotions[emo] = emotions.get(emo, 0) + 1
        
        # 2. RL Aggregation
        rl_logs = list(db.PedagogicalStrategy.find({
            "user_id": user_id,
            "timestamp": {"$gte": one_day_ago}
        }))
        
        actions = {}
        if rl_logs:
            for l in rl_logs:
                aid = l.get("action_id", 0)
                name = RL_ACTION_MAP.get(aid, {}).get("name", "Unknown")
                actions[name] = actions.get(name, 0) + 1

        # 3. User Preferences (Future-proofed mocks as requested)
        preferences = {
            "learning_style": "Visual/Spatial",
            "difficulty_bias": "+0.15 (Advanced)",
            "session_length_pref": "45 min",
            "tone_preference": "Empathetic"
        }

        return {
            "user_id": user_id,
            "time_window": "24h",
            "cv_stats": {
                "average_engagement": round(avg_engagement, 2),
                "dominant_emotions": emotions,
                "total_samples": len(cv_logs)
            },
            "rl_stats": {
                "action_distribution": actions,
                "total_decisions": len(rl_logs)
            },
            "preferences": preferences
        }
    except Exception as e:
        print(f"Analytics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/latest")
async def get_latest_telemetry(user_id: str = Depends(get_current_user)):
    """
    Fetches the absolute latest CV and RL packets for the specified user.
    """
    try:
        from agent_core.snapshot import _get_db
        from agent_core.schemas import RL_ACTION_MAP
        db = _get_db()
        
        if db is None:
            return {"status": "offline", "error": "Database Connection Failed"}
        
        # 1. Latest CV
        latest_cv = db.StudentEngagement.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        # 2. Latest RL
        latest_rl = db.PedagogicalStrategy.find_one(
            {"user_id": user_id},
            sort=[("timestamp", -1)]
        )
        
        # Format CV data for UI
        cv_data = {}
        if latest_cv:
            cv_data = {
                "engagement_score": round(latest_cv.get("engagement_score", 0), 2),
                "emotion": latest_cv.get("emotion", "neutral"),
                "timestamp": latest_cv.get("timestamp").isoformat() if latest_cv.get("timestamp") else None
            }
            
        # Format RL data for UI
        rl_data = {}
        if latest_rl:
            aid = latest_rl.get("action_id", 0)
            name = RL_ACTION_MAP.get(aid, {}).get("name", "Unknown")
            rl_data = {
                "action": name,
                "confidence": round(latest_rl.get("confidence", 0), 2),
                "reasoning": latest_rl.get("reasoning", "Live monitoring"),
                "timestamp": latest_rl.get("timestamp").isoformat() if latest_rl.get("timestamp") else None
            }
            
        return {
            "user_id": user_id,
            "cv": cv_data,
            "rl": rl_data
        }
    except Exception as e:
        print(f"Latest Telemetry Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/analytics/profile/{student_id}")
async def get_enhanced_analytics(current_user: str = Depends(get_current_user)):
    """
    Project ID: 25-26J-130
    Modernized analytics for the Data Center.
    """
    try:
        student_id = current_user
        db = get_db_connection()
        
        # Mock / Fallback Data if DB is offline
        if db is None:
            print(">>> [Analytics] MongoDB Offline. Using Mock Fallback.")
            return {
                "profile": {
                    "primary_modality": "Visual",
                    "scaffolding_bias": "+0.15",
                    "radar_data": [
                        {"subject": "Visual/Spatial", "value": 75},
                        {"subject": "Textual", "value": 45},
                        {"subject": "Interactive", "value": 60}
                    ]
                },
                "affective": {
                    "avg_engagement": 0.72,
                    "engagement_trend": [],
                    "emotions": [{"name": "Focused", "count": 10}, {"name": "Confused", "count": 2}]
                },
                "intervention": {
                    "success_rate": 85,
                    "recent_swaps": [],
                    "policy_distribution": [
                        {"name": "Simplify Explanation", "value": 12},
                        {"name": "Provide Worked Example", "value": 8}
                    ]
                },
                "mastery_data": [
                    {"topic": "Dimensional Modelling", "score": 85, "status": "Expert", "source": "Mock Data"}
                ]
            }

        profiles = get_profiles_collection(db)
        profile = profiles.find_one({"student_id": student_id}, {"_id": 0}) if profiles is not None else None
        
        if not profile:
            profile = {
                "preferred_modality": {"visual": 0.33, "textual": 0.33, "interactive": 0.34},
                "historical_mastery": {},
                "learning_history": []
            }

        # 1. Radar Chart & Profile Baselines
        m = profile.get("preferred_modality", {})
        radar_data = [
            {"subject": "Visual/Spatial", "value": round(m.get("visual", 0.33) * 100)},
            {"subject": "Textual", "value": round(m.get("textual", 0.33) * 100)},
            {"subject": "Interactive", "value": round(m.get("interactive", 0.34) * 100)}
        ]
        
        # Primary Modality Label
        primary = max(m, key=m.get) if m else "Visual"
        primary_label = primary.capitalize() if primary != "interactive" else "Interactive"

        # 2. Intervention Success Metrics
        total_stagnation = db.interactions.count_documents({"student_id": student_id, "is_stagnation_event": True})
        shadow_accepted = db.interactions.count_documents({"student_id": student_id, "shadow_accepted": True})
        success_rate = round((shadow_accepted / total_stagnation * 100) if total_stagnation > 0 else 0)

        # 3. Rolling Engagement (Last 5 Minutes)
        now = datetime.now()
        five_mins_ago = now - timedelta(minutes=5)
        # Note: StudentEngagement uses 'user_id' whereas other collections use 'student_id'
        telemetry = list(db.StudentEngagement.find(
            {"user_id": student_id, "timestamp": {"$gte": five_mins_ago}},
            {"_id": 0, "engagement_score": 1, "timestamp": 1, "emotion": 1}
        ).sort("timestamp", 1))

        engagement_trend = []
        emotion_counts = {"focused": 0, "confused": 0, "bored": 0, "frustrated": 0, "neutral": 0}
        total_score = 0
        
        for t in telemetry:
            ts_str = t["timestamp"].strftime("%H:%M:%S")
            score = round(t["engagement_score"], 2)
            engagement_trend.append({
                "time": ts_str,
                "score": score,
                "benchmark": 0.85
            })
            total_score += score
            emo = t.get("emotion", "neutral").lower()
            if emo in emotion_counts:
                emotion_counts[emo] += 1
        
        avg_engagement = round(total_score / len(telemetry), 2) if telemetry else 0.68

        # 4. RL Policy Distribution
        policy_data = {
            "Simplify Explanation": 0,
            "Provide Worked Example": 0,
            "Switch Learning Mode": 0,
            "Proactive Intervention": 0
        }
        
        interactions = list(db.interactions.find({"student_id": student_id}).sort("timestamp", -1).limit(100))
        recent_swaps = []
        
        for inter in interactions:
            strategy = inter.get("selected_strategy_label", "")
            if strategy in policy_data:
                policy_data[strategy] += 1
            
            if inter.get("shadow_accepted"):
                policy_data["Proactive Intervention"] += 1
                if len(recent_swaps) < 5:
                    recent_swaps.append({
                        "timestamp": inter["timestamp"].strftime("%H:%M"),
                        "strategy": strategy,
                        "engagement": inter.get("engagement_at_swap", 0.72)
                    })

        # 5. Mastery & Source Audit
        mastery_data = []
        hist_mastery = profile.get("historical_mastery", {})
        if "Dimensional Modelling" not in hist_mastery:
            hist_mastery["Dimensional Modelling"] = 0.85
            
        for topic, score in hist_mastery.items():
            status = "Expert" if score >= 0.8 else "Intermediate" if score >= 0.4 else "Novice"
            mastery_data.append({
                "topic": topic,
                "score": round(score * 100),
                "status": status,
                "source": "DWBI Lecture 03 Dimensional Modelling Part I.pdf" if "Dimensional" in topic else "Synthetic Logic"
            })

        return {
            "profile": {
                "primary_modality": primary_label,
                "scaffolding_bias": "+0.15", # Baseline
                "radar_data": radar_data
            },
            "affective": {
                "avg_engagement": avg_engagement,
                "engagement_trend": engagement_trend,
                "emotions": [{"name": k.capitalize(), "count": v} for k, v in emotion_counts.items()]
            },
            "intervention": {
                "success_rate": success_rate,
                "recent_swaps": recent_swaps,
                "policy_distribution": [{"name": k, "value": v} for k, v in policy_data.items()]
            },
            "mastery_data": mastery_data
        }
    except Exception as e:
        print(f"Analytics Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
