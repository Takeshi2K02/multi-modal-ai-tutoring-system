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

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str
    birthday: str
    role: str
    preferred_learning_style: str
    interested_areas: List[str]
    strengths: List[str]
    weaknesses: List[str]

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/api/auth/register")
async def register(req: RegisterRequest):
    db = get_db_connection()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    users = db["users"]
    if users.find_one({"email": req.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash the password on the backend before storing
    hashed_password = get_password_hash(req.password)
    
    # Store full document exactly as requested
    user_doc = {
        "full_name": req.full_name,
        "email": req.email,
        "password_hash": hashed_password, 
        "personal_info": {
            "birthday": req.birthday,
            "role": req.role
        },
        "learning_profile": {
            "preferred_learning_style": req.preferred_learning_style,
            "interested_areas": req.interested_areas,
            "strengths": req.strengths,
            "weaknesses": req.weaknesses
        },
        "created_at": datetime.utcnow()
    }
    
    users.insert_one(user_doc)
    return {"status": "success", "message": "User created"}

@router.post("/api/auth/login")
async def login(req: LoginRequest):
    db = get_db_connection()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    users = db["users"]
    user = users.find_one({"email": req.email})
    
    # Secure verification using bcrypt
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user["email"]}
