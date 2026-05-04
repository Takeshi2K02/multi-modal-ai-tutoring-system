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

class QuizSubmitRequest(BaseModel):
    subtopic: str
    score: float
    mastery_level: Optional[float] = 0.5

@router.post("/api/session/quiz-submit")
async def submit_quiz(req: QuizSubmitRequest, current_user: str = Depends(get_current_user)):
    try:
        from services.learning_session_service import record_performance
        record_performance(current_user, {
            "quiz_score": req.score,
            "subtopic": req.subtopic,
            "mastery_level": req.mastery_level
        })
        return {"status": "recorded", "student_id": current_user}
    except Exception as e:
        print(f"[Server] WARNING: record_performance failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class ChallengeRequest(BaseModel):
    student_id: str
    session_id: str
    topic_id: str
    response: str
    context: Optional[str] = ""

class PerformanceRecord(BaseModel):
    student_id: str
    session_id: str
    topic_id: str
    score: float
    total_questions: int
    correct_answers: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GeneratedContentRequest(BaseModel):
    student_id: str
    session_id: str
    topic_id: str
    content: Optional[Dict[str, Any]] = None

class StudentProgressRequest(BaseModel):
    student_id: str
    session_id: str
    topic_id: str
    content: Dict[str, Any]
    user_response: Optional[str] = None
    ai_evaluation_score: Optional[float] = None

@router.post("/api/performance/save")
async def save_performance(record: PerformanceRecord):
    try:
        service = LearningSessionService()
        success = service.save_performance_record(record.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save performance record")
        return {"status": "success"}
    except Exception as e:
        print(f"Save Performance Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/lesson/content")
async def get_lesson_content(student_id: str, topic_id: str, session_id: Optional[str] = None):
    try:
        service = LearningSessionService()
        content = service.get_generated_content(student_id, topic_id, session_id)
        return {"content": content}
    except Exception as e:
        print(f"Get Lesson Content Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/lesson/save_content")
async def save_lesson_content(req: GeneratedContentRequest):
    try:
        service = LearningSessionService()
        success = service.save_generated_content(req.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save lesson content")
        return {"status": "success"}
    except Exception as e:
        print(f"Save Generated Content Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/lesson/sync_progress")
async def sync_student_progress(request: StudentProgressRequest):
    try:
        service = LearningSessionService()
        success = service.save_student_progress(request.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to sync student progress")
        return {"status": "success"}
    except Exception as e:
        print(f"Sync Progress Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/challenge/evaluate")
async def evaluate_challenge(req: ChallengeRequest):
    """
    Evaluates a design challenge response using Gemini 2.5 Flash.
    """
    try:
        from agent_core.llm import get_llm
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        import json

        llm = get_llm()
        
        prompt = PromptTemplate(
            template="""
            Role: Pedagogical Expert & Design Reviewer.
            
            Lesson Context: {context}
            Topic: {topic}
            Student Response: {response}
            
            TASK: Evaluate if the student's 3-5 attributes are valid and insightful based on the context.
            
            JSON FORMAT:
            {{
                "score": float (0.0 - 1.0),
                "feedback": "Concise, encouraging, and critical feedback",
                "alignment_check": boolean
            }}
            """,
            input_variables=["context", "topic", "response"]
        )
        
        chain = prompt | llm | StrOutputParser()
        raw_res = await chain.ainvoke({
            "context": req.context,
            "topic": req.topic_id,
            "response": req.response
        })
        
        # Simple parser for JSON extraction
        import re
        match = re.search(r"(\{.*\})", raw_res, re.DOTALL)
        res_data = json.loads(match.group(1)) if match else {"score": 0.5, "feedback": "Synthesis in progress.", "alignment_check": True}

        # Save to MongoDB
        service = LearningSessionService()
        record = {
            "student_id": req.student_id,
            "session_id": req.session_id,
            "topic_id": req.topic_id,
            "score": res_data.get("score", 0.0) * 100,
            "feedback": res_data.get("feedback", ""),
            "type": "CHALLENGE",
            "timestamp": datetime.now()
        }
        service.save_performance_record(record)
        service.update_session_progress(req.session_id, req.topic_id)
        
        return res_data
    except Exception as e:
        print(f"Challenge Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
