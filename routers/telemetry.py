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

class CVTelemetryRequest(BaseModel):
    user_id: str
    engagement_score: float
    emotion: str
    gaze: Optional[str] = "unknown"
    posture: Optional[str] = "unknown"
    engagement_state: Optional[str] = "unknown"
    interaction_id: Optional[str] = None
    metadata: Optional[Dict] = None

class CVTrackRequest(BaseModel):
    frame: str
    user_id: str
    material_id: Optional[str] = None
    interaction_id: Optional[str] = None

class RLTelemetryRequest(BaseModel):
    user_id: str
    action_id: int
    confidence: float
    reasoning: Optional[str] = None

@router.post("/api/engagement/track")
async def track_engagement_direct(req: CVTrackRequest):
    """
    Direct hook for webcam frames. Processes and emits for Admin Monitor.
    """
    try:
        # print(f">>> CV Frame Received. PID={os.getpid()} Exec={sys.executable}")
        # print(f">>> Current sys.path: {sys.path[:3]}...") # Log start of path

        from services.engagement_service import process_engagement_data
        from integration.persistence import push_cv_data

        # Process via CV module services
        result = process_engagement_data(req.frame, material_id=req.material_id)
        
        # Persist and Emit (push_cv_data handles socket emission now)
        await push_cv_data(
            req.user_id, 
            result['engagement_score'], 
            result['emotion'],
            gaze=result.get('gaze', 'unknown'),
            posture=result.get('posture', 'unknown'),
            engagement_state=result.get('engagement_state', 'unknown'),
            interaction_id=req.interaction_id,
            metadata=result
        )
        
        return result
    except Exception as e:
        print(f"Direct CV Hook Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@router.post("/api/telemetry/cv")
async def receive_cv_telemetry(req: CVTelemetryRequest):
    # print(f">>> CV Telemetry Received: User={req.user_id}, Score={req.engagement_score}, Emotion={req.emotion}")
    from integration.persistence import push_cv_data
    await push_cv_data(
        req.user_id, 
        req.engagement_score, 
        req.emotion, 
        gaze=req.gaze, 
        posture=req.posture, 
        engagement_state=req.engagement_state, 
        interaction_id=req.interaction_id,
        metadata=req.metadata
    )
    return {"status": "telemetry_logged"}

@router.post("/api/telemetry/rl")
async def receive_rl_telemetry(req: RLTelemetryRequest):
    # print(f">>> RL Telemetry Received: User={req.user_id}, Action={req.action_id}, Conf={req.confidence}")
    from integration.persistence import push_rl_strategy
    await push_rl_strategy(req.user_id, req.action_id, req.confidence, req.reasoning)
    return {"status": "telemetry_logged"}
