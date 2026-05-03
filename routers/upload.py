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

class DecomposeRequest(BaseModel):
    goal: str
    collection_id: Optional[str] = None # Phase 21: RAG Isolation

@router.post("/api/goal_decompose")
async def goal_decompose(req: DecomposeRequest, user_id: str = Depends(get_current_user)):
    print(f"Decomposing goal: {req.goal} (Collection: {req.collection_id}) for User: {user_id}")
    try:
        result = decompose_goal(req.goal, req.collection_id, user_id)
        return result
    except Exception as e:
        print(f"Decomposition Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...), 
    collection_id: Optional[str] = Query(None),
    plan_id: Optional[str] = Query(None) # Issue 1: Write back to plan
):
    """
    Ingests PDF, DOCX, PPTX, or TXT into the Local VectorDB.
    """
    print(f"Received upload: {file.filename} (Collection: {collection_id}, Plan: {plan_id})")
    try:
        allowed_extensions = {".pdf", ".docx", ".pptx", ".txt"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}")
            
        content = await file.read()
        result = await ingest_document(content, file.filename, collection_id, plan_id)
        return result
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analyze-anatomy")
async def analyze_anatomy(file: UploadFile = File(...)):
    """
    Analyzes the anatomy of a PDF file and returns a summary.
    """
    print(f"Received analysis request: {file.filename}")
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
            
        content = await file.read()
        result = await analyze_pdf_anatomy(content, file.filename)
        return result
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/download-summary/{filename}")
async def download_summary(filename: str):
    """
    Serves the generated anatomy summary .txt files.
    """
    summary_path = os.path.join(BASE_DIR, "local_data", "summaries", filename)
    if not os.path.exists(summary_path):
        raise HTTPException(status_code=404, detail="Summary file not found.")
    
    return FileResponse(
        path=summary_path,
        media_type="text/plain",
        filename=filename
    )
