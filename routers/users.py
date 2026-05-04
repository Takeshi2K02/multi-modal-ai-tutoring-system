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

class UserFeedbackRequest(BaseModel):
    student_id: str
    interaction_id: Optional[str] = None
    action_type: str # e.g. "SIMPLIFY_EXPLANATION"
    sentiment: bool # true = Up, false = Down
    modality_type: str # "visual" | "textual" | "interactive"
    topic_id: Optional[str] = None

@router.post("/api/user/feedback")
async def handle_user_feedback(req: UserFeedbackRequest):
    """
    Updates student preferences based on Thumbs Up/Down.
    """
    try:
        db = get_db_connection()
        profiles = get_profiles_collection(db)
        
        # 1. Update Profile or create if missing
        profile = profiles.find_one({"student_id": req.student_id})
        if not profile:
            profile = {
                "student_id": req.student_id,
                "preferred_modality": {"visual": 0.33, "textual": 0.33, "interactive": 0.34},
                "historical_mastery": {},
                "engagement_baseline": 0.5,
                "learning_history": []
            }
            profiles.insert_one(profile)
            
        # 2. Update Weights
        weights = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
        
        increment = 0.05 if req.sentiment else -0.05
        target_modality = req.modality_type.lower()
        
        if target_modality in weights:
            weights[target_modality] = max(0.1, min(0.8, weights.get(target_modality, 0.33) + increment))
            
            # Special Rule: Positive feedback on SIMPLIFY_EXPLANATION + Visual 
            # also boosts textual (simple) weight
            if req.sentiment and req.action_type == "SIMPLIFY_EXPLANATION" and target_modality == "visual":
                weights["textual"] = max(0.1, min(0.8, weights.get("textual", 0.33) + 0.05))

        # Normalize weights
        total = sum(weights.values())
        for k in weights:
            weights[k] = round(weights[k] / total, 2)
            
        # 3. Handle Strategy Blacklist (Project ID: 25-26J-130)
        blacklist_update = {}
        if not req.sentiment and req.topic_id:
            blacklist = profile.get("strategy_blacklist", {})
            if req.topic_id not in blacklist:
                blacklist[req.topic_id] = []
            if req.action_type not in blacklist[req.topic_id]:
                blacklist[req.topic_id].append(req.action_type)
            blacklist_update = {"strategy_blacklist": blacklist}

        # 4. Save Profile Updates
        update_data = {"preferred_modality": weights}
        if blacklist_update:
            update_data.update(blacklist_update)

        profiles.update_one(
            {"student_id": req.student_id},
            {
                "$set": update_data,
                "$push": {
                    "learning_history": {
                        "timestamp": datetime.now(),
                        "action_taken": req.action_type,
                        "user_feedback": 1 if req.sentiment else -1
                    }
                }
            }
        )

        # 5. Update Interaction Outcome (Project ID: 25-26J-130)
        if req.interaction_id:
            outcome = "Positive" if req.sentiment else "Negative"
            
            # Project ID: 25-26J-130: Robust ID handling for syn-* strings
            try:
                db_id = ObjectId(req.interaction_id)
            except Exception:
                db_id = req.interaction_id

            db.interactions.update_one(
                {"_id": db_id},
                {"$set": {"outcome": outcome}}
            )
            
        # 6. Write Feedback Signal for DQN State Vector (Project ID: 25-26J-130)
        db.FeedbackSignals.insert_one({
            "student_id": req.student_id,
            "interaction_id": req.interaction_id,
            "topic_id": req.topic_id,
            "signal": 1.0 if req.sentiment else -1.0,
            "timestamp": datetime.now()
        })
        
        return {"status": "success", "new_weights": weights}
    except Exception as e:
        print(f"Feedback Update Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class AcceptShadowRequest(BaseModel):
    student_id: str
    interaction_id: str
    modality_type: str
    action_type: str
    topic_id: str

@router.post("/api/user/accept_shadow")
async def accept_shadow_intervention(req: AcceptShadowRequest):
    """
    Handles user acceptance of a shadow intervention.
    Project ID: 25-26J-130
    """
    try:
        db = get_db_connection()
        profiles = get_profiles_collection(db)
        
        # 1. Mark shadow as accepted in interactions
        from bson import ObjectId
        # Project ID: 25-26J-130: Robust ID handling for syn-* strings
        try:
            db_id = ObjectId(req.interaction_id)
        except Exception:
            db_id = req.interaction_id

        db.interactions.update_one(
            {"_id": db_id},
            {"$set": {"shadow_accepted": True}}
        )
        
        # 2. Update Student Profile Weights (+0.05 focus)
        profile = profiles.find_one({"student_id": req.student_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
            
        weights = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
        target = req.modality_type.lower()
        
        if target in weights:
            # Boost the accepted modality
            weights[target] = max(0.1, min(0.85, weights.get(target, 0.33) + 0.05))
            
            # Normalize
            total = sum(weights.values())
            for k in weights:
                weights[k] = round(weights[k] / total, 2)
                
            profiles.update_one(
                {"student_id": req.student_id},
                {"$set": {"preferred_modality": weights}}
            )
            
            # 3. Emit real-time profile updated event
            from socket_manager import sio
            import core.state
            core.state.waiting_for_user_decision[req.student_id] = 0

            await sio.emit("profile_updated", {
                "student_id": req.student_id,
                "modality": target,
                "delta": 0.05,
                "new_weights": weights
            })
            
        return {"status": "success", "new_weights": weights}
    except Exception as e:
        print(f"Shadow Acceptance Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/user/profile/{student_id}")
async def get_user_profile(current_user: str = Depends(get_current_user)):
    """
    Fetches student profile data.
    """
    try:
        student_id = current_user
        db = get_db_connection()
        profiles = get_profiles_collection(db)
        
        profile = profiles.find_one({"student_id": student_id}, {"_id": 0})
        if not profile:
            return {
                "student_id": student_id,
                "preferred_modality": {"visual": 0.33, "textual": 0.33, "interactive": 0.34},
                "historical_mastery": {},
                "engagement_baseline": 0.5,
                "learning_history": []
            }
        return profile
    except Exception as e:
        print(f"Profile Fetch Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
