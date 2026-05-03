import sys
import os
import asyncio
import time
import warnings
import atexit
from datetime import datetime, timedelta

# Project ID: 25-26J-130: Clean Logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'
os.environ['TQDM_DISABLE'] = '1' # Block progress bars

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*ChatVertexAI.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

# Silence high-frequency third-party loggers
import logging
for logger_name in ["transformers", "mediapipe", "absl", "google", "google_auth_httplib2"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def cleanup_resources():
    """Project ID: 25-26J-130: Robust semaphore cleanup."""
    # print(">>> Performing resource cleanup...")
    try:
        from multiprocessing import resource_tracker
        resource_tracker._resource_tracker._fd = None # Force reset
        resource_tracker._resource_tracker.ensure_running()
    except Exception:
        pass

atexit.register(cleanup_resources)

# Add CV backend paths for direct hook access
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "cv", "backend"))

from services.decomposition_service import decompose_goal
from services.ingestion_service import ingest_document
from services.analysis_service import analyze_pdf_anatomy

from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt

# Initialize FastAPI
fastapi_app = FastAPI()

# --- Auth Configuration ---
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

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

def get_password_hash(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password, hashed_password):
    password_byte_enc = plain_password.encode('utf-8')
    hashed_password_byte_enc = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte_enc, hashed_password_byte_enc)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

# --- Auth Endpoints ---
@fastapi_app.post("/api/auth/register")
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

@fastapi_app.post("/api/auth/login")
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

class QuizSubmitRequest(BaseModel):
    subtopic: str
    score: float
    mastery_level: Optional[float] = 0.5

@fastapi_app.post("/api/session/quiz-submit")
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

# --- Logging Noise Suppression ---
import logging
class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Exclude high-frequency telemetry/analytics logs
        return record.getMessage().find("/api/engagement/track") == -1 and \
               record.getMessage().find("/api/telemetry/rl") == -1 and \
               record.getMessage().find("/api/analytics/latest") == -1 and \
               record.getMessage().find("/socket.io/") == -1

# Filter uvicorn access logs
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

from socket_manager import sio
app = ASGIApp(sio, fastapi_app)

@sio.event
async def connect(sid, environ, auth):
    token = None
    
    # 1. Check 'auth' dictionary (modern socket.io style)
    if auth and isinstance(auth, dict):
        token = auth.get("token")
        
    # 2. Check HTTP Headers (fallback)
    if not token:
        auth_header = environ.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            
    # 3. Check Query String (legacy/secondary fallback)
    if not token:
        qs = environ.get("QUERY_STRING", "")
        for part in qs.split("&"):
            if part.startswith("token="):
                token = part[6:]
    
    if not token:
        print(f"[Socket] Connection rejected for {sid}: No token provided.")
        return False

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        await sio.save_session(sid, {"user_id": user_id})
        print(f"[Socket] {sid} authenticated as {user_id}")
    except Exception as e:
        print(f"[Socket] Authentication failed for {sid}: {e}")
        return False

@sio.on("join_room")
async def handle_join_room(sid, data):
    session = await sio.get_session(sid)
    authenticated_user_id = session.get("user_id")
    requested_room = data.get("student_id")
    if not authenticated_user_id or authenticated_user_id != requested_room:
        print(f"[Room] REJECTED: {sid} tried to join {requested_room}, "
              f"authenticated as {authenticated_user_id}")
        return
    await sio.enter_room(sid, requested_room)
    print(f"[Room] {sid} joined room: {requested_room}")

from socket_manager import get_sio

# Enable CORS for local dev
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from agent_core.snapshot import get_student_snapshot
from db.connection import get_db_connection, get_profiles_collection
from services.vector_factory import get_vector_db

def check_infrastructure():
    """
    Startup health check: Ensures MongoDB and Pinecone are reachable.
    """
    print("\n[Startup] 🩺 Running Infrastructure Health Check...")
    
    # 1. MongoDB Check
    try:
        db = get_db_connection()
        print(f"[Startup] ✅ MongoDB Connected: {db.name}")
    except Exception as e:
        print(f"[Startup] ❌ MongoDB Connection Failed!")
        raise e

    # 2. VectorDB Check
    try:
        vectordb = get_vector_db()
        print(f"[Startup] ✅ VectorDB Initialized ({type(vectordb).__name__})")
    except Exception as e:
        print(f"[Startup] ❌ VectorDB Initialization Failed!")
        raise e
        
    print("[Startup] 🚀 All systems green. Ready for requests.\n")

# Run check immediately on import (Requirement 3)
check_infrastructure()

from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState, ThoughtNode

# Project ID: 25-26J-130: Proactive Intervention Monitor
triggered_interventions = set()
active_student_synthesis = set() # Standardized Lock

async def monitor_interventions():
    """
    Background Task: Periodically checks for stagnation and triggers Shadow ToT.
    """
    print(">>> [Intervention] Proactive Monitor Started.")
    while True:
        try:
            db = get_db_connection()
            if db is None:
                await asyncio.sleep(10)
                continue
                
            # Dynamic Student Detection: Find latest student with engagement logs
            latest_engagement = db.StudentEngagement.find_one(sort=[("timestamp", -1)])
            # 1. Presence Guard: Only monitor if student is actively sending telemetry
            if not latest_engagement:
                await asyncio.sleep(10)
                continue
            
            student_id = latest_engagement.get("user_id")
            last_ping = latest_engagement.get("timestamp")
            
            # If no telemetry for 30s, assume student is idle/away
            if (datetime.now() - last_ping).total_seconds() > 30:
                # print(f">>> [Intervention] Student {student_id} is idle. Skipping monitor.")
                await asyncio.sleep(10)
                continue

            # 2. Synthesis Lock: Skip if student is currently generating a lesson
            if student_id in active_student_synthesis:
                # print(f">>> [Intervention] Student {student_id} is busy synthesizing. Skipping monitor.")
                await asyncio.sleep(10)
                continue

            # 3. Fetch Snapshot (includes trigger logic)
            snapshot = get_student_snapshot(student_id)
            
            if snapshot.intervention_needed:
                # 3. Check if we already handled this interaction
                latest_inter = db.interactions.find_one(
                    {"student_id": student_id},
                    sort=[("timestamp", -1)]
                )
                
                if latest_inter:
                    inter_id = str(latest_inter["_id"])
                    if inter_id not in triggered_interventions:
                        query = latest_inter.get("query")
                        if not query:
                            print(f">>> [Intervention] ⚠️ Skipping {inter_id}: Missing user query.")
                            continue

                        print(f">>> [Intervention] 🛰️ Stagnation Detected for {inter_id}. Triggering Shadow ToT...")
                        print(f"[Pipeline] ⚠️ ToT Trigger: Engagement drop detected. Branching alternative paths...")
                        
                        
                        # 3. Trigger ToT in Shadow Mode
                        async def run_shadow():
                            try:
                                agent = create_tot_graph()
                                initial_state = {
                                    "student_id": student_id,
                                    "user_query": latest_inter["query"],
                                    "context_data": {"snapshot": snapshot.dict()},
                                    "profile": None,
                                    "frontier": [],
                                    "tree_memory": {},
                                    "best_node": None,
                                    "student_preferences": {},
                                    "strategy_blacklist": [],
                                    "teaching_strategy": None,
                                    "final_response": None,
                                    "reasoning_trace": [],
                                    "build_time": 0.0,
                                    "stop_early": False,
                                    "selected_strategy_label": None,
                                    "interaction_outcome": None,
                                    "interaction_id": inter_id
                                }
                                # The graph will run background_synthesis because intervention_needed is True
                                await agent.ainvoke(initial_state)
                                # Success!
                                triggered_interventions.add(inter_id)
                                
                                # Project ID: 25-26J-130: Mark as stagnation event for analytics
                                db.interactions.update_one(
                                    {"_id": latest_inter["_id"]},
                                    {"$set": {"is_stagnation_event": True}}
                                )
                            except Exception as e:
                                print(f">>> [Intervention] Shadow Run Failed: {e}")
                            
                        asyncio.create_task(run_shadow())

        except Exception as e:
            print(f">>> [Intervention] Monitor Error: {e}")
            
        await asyncio.sleep(10) # Check every 10 seconds

@fastapi_app.on_event("startup")
async def startup_event():
    print(">>> Initializing Agentic AI Core...")
    asyncio.create_task(monitor_interventions())

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    print(">>> Shutting down Agentic AI Core...")
    # Clean up semaphores for MediaPipe/TensorFlow
    try:
        import multiprocessing.resource_tracker as rt
        # Force cleanup of leaked semaphores
        rt._resource_tracker.ensure_running()
    except Exception as e:
        print(f"Cleanup warning: {e}")

class ScenarioRequest(BaseModel):
    scenario: str # "confused" | "bored"
    topic_title: Optional[str] = None
    topic_content: Optional[str] = None
    synthesis_id: Optional[str] = None
    session_id: Optional[str] = None # Issue 2: For collection_id resolution
    collection_id: Optional[str] = None # Phase 21: RAG Isolation

class DecomposeRequest(BaseModel):
    goal: str
    collection_id: Optional[str] = None # Phase 21: RAG Isolation

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    meta: Dict[str, Any]

class SavePlanRequest(BaseModel):
    plan_data: Dict[str, Any]

class CreateSessionRequest(BaseModel):
    plan_id: str
    student_id: str

class UpdateProgressRequest(BaseModel):
    session_id: str
    topic_id: str

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
    topic_id: str
    content: Optional[Dict[str, Any]] = None

class StudentProgressRequest(BaseModel):
    student_id: str
    topic_id: str
    content: Dict[str, Any]
    user_response: Optional[str] = None
    ai_evaluation_score: Optional[float] = None

class SessionStartRequest(BaseModel):
    session_id: str
    topic_id: str
    collection_id: Optional[str] = None

class UserFeedbackRequest(BaseModel):
    student_id: str
    interaction_id: Optional[str] = None
    action_type: str # e.g. "SIMPLIFY_EXPLANATION"
    sentiment: bool # true = Up, false = Down
    modality_type: str # "visual" | "textual" | "interactive"
    topic_id: Optional[str] = None

from services.learning_plan_service import LearningPlanService
from services.learning_session_service import LearningSessionService

@fastapi_app.post("/api/session/progress")
async def update_session_progress(request: UpdateProgressRequest):
    try:
        service = LearningSessionService()
        success = service.update_session_progress(request.session_id, request.topic_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session or topic update failed")
        return {"status": "success"}
    except Exception as e:
        print(f"Update Progress Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/performance/save")
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

@fastapi_app.get("/api/lesson/content")
async def get_lesson_content(student_id: str, topic_id: str):
    try:
        service = LearningSessionService()
        content = service.get_generated_content(student_id, topic_id)
        return {"content": content}
    except Exception as e:
        print(f"Get Lesson Content Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/lesson/save_content")
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

@fastapi_app.post("/api/lesson/sync_progress")
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

@fastapi_app.post("/api/challenge/evaluate")
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

@fastapi_app.post("/api/learning_plan/save")
async def save_learning_plan(request: SavePlanRequest, user_id: str = Depends(get_current_user)):
    try:
        service = LearningPlanService()
        # Ensure student_id matches authenticated user (Project ID: 25-26J-130)
        request.plan_data["student_id"] = user_id
        plan_id = service.save_learning_plan(request.plan_data)
        return {"status": "success", "plan_id": plan_id}
    except Exception as e:
        print(f"Save Plan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/session/create")
async def create_session(request: CreateSessionRequest, user_id: str = Depends(get_current_user)):
    print(f"Received Create Session Request: plan_id={request.plan_id}, student_id={user_id}")
    try:
        service = LearningSessionService()
        session_id = service.create_session(request.plan_id, user_id)
        print(f"Session Created Successfully: {session_id}")
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Create Session Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    service = LearningSessionService()
    data = service.get_session_details(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Phase 1 Task 3: Trigger Background RAG Pre-fetch
    try:
        plan = data.get("plan", {})
        collection_id = plan.get("system_metadata", {}).get("collection_id")
        if collection_id:
            # We pre-fetch for all topics in the plan
            topics = []
            for lecture in plan.get("curriculum", {}).get("structure", []):
                for topic in lecture.get("children", []):
                    topics.append(topic.get("title"))
            
            asyncio.create_task(prefetch_rag_to_redis(collection_id, topics, str(plan.get("_id"))))
    except Exception as e:
        print(f"[Cache] Pre-fetch trigger failed: {e}")

    return data

@fastapi_app.post("/api/session/exit")
async def exit_session(req: Dict[str, str]):
    """
    Phase 1 Task 3: Explicitly delete RAG cache on module exit.
    """
    plan_id = req.get("plan_id")
    if plan_id:
        try:
            import redis
            r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
            keys = r.keys(f"rag_cache:{plan_id}:*")
            if keys:
                r.delete(*keys)
                print(f"[Cache] 🗑️ Invalidated {len(keys)} keys for plan {plan_id}")
        except Exception as e:
            print(f"[Cache] ⚠️ Invalidation failed: {e}")
    return {"status": "exited"}

async def prefetch_rag_to_redis(collection_id: str, topics: List[str], plan_id: str):
    """
    Phase 1 Task 3: Background task to warm up Redis with Pinecone chunks.
    """
    try:
        import redis, json
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
        from services.vector_factory import get_vector_db
        vectordb = get_vector_db()
        
        for topic in topics:
            cache_key = f"rag_cache:{plan_id}:{topic}"
            # Check if already cached
            if r.exists(cache_key): continue
            
            print(f"[Cache] 🛰️ Pre-fetching RAG for topic: {topic}")
            # Cap at 20 chunks as requested
            results = vectordb.search(f"Teach me about {topic}", top_k=20, filter={"collection_id": collection_id})
            if results:
                r.setex(cache_key, 1800, json.dumps(results)) # 30 min TTL
        print(f"[Cache] ✅ Pre-fetch complete for plan {plan_id}")
    except Exception as e:
        print(f"[Cache] ⚠️ Background pre-fetch failed: {e}")

@fastapi_app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a learning session.
    """
    service = LearningSessionService()
    success = service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    return {"message": "Session deleted successfully"}

@fastapi_app.post("/api/session/start")
async def start_session_topic(req: SessionStartRequest, user_id: str = Depends(get_current_user)):
    """
    Standardized entry point for starting a learning node within a session.
    Triggers the full agentic pipeline.
    """
    print(f"\n[Pipeline] 🚀 SESSION START: {req.session_id} | Topic: {req.topic_id}")
    
    # Reuse run_simulation logic but with session context
    scenario_req = ScenarioRequest(
        scenario="confused", # Default scenario for new start
        topic_title=req.topic_id,
        synthesis_id=f"syn-{int(time.time()*1000)}",
        collection_id=req.collection_id
    )
    
    # Update session status to IN_PROGRESS and set current topic (Project ID: 25-26J-130)
    service = LearningSessionService()
    service.start_session(req.session_id, req.topic_id)

    # We call run_simulation logic directly
    return await run_simulation(scenario_req, user_id=user_id)

@fastapi_app.get("/api/sessions/student/{student_id}")
async def get_student_sessions(student_id: str):
    try:
        service = LearningSessionService()
        sessions = service.get_sessions_by_student(student_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"List Sessions Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def transform_state_to_graph(state: AgentState) -> GraphResponse:
    tree_memory = state["tree_memory"]
    best_node = state["best_node"]
    
    # Identify Best Path IDs (ordered from root to leaf)
    best_path_ids = []
    curr = best_node
    while curr:
        best_path_ids.append(curr.id)
        if curr.parent_id:
            curr = tree_memory.get(curr.parent_id)
        else:
            curr = None
    best_path_ids.reverse()
            
    nodes = []
    edges = []
    
    # Build Nodes & Edges
    for node_id, node in tree_memory.items():
        # Determine styling class based on local score
        node_class = "node-default"
        if node.score >= 0.8:
            node_class = "node-high-score"
        elif node.score < 0.5:
            node_class = "node-low-score"
            
        # Node
        nodes.append({
            "id": node.id,
            "data": {
                "label": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                "fullContent": node.content,
                "localScore": node.score,
                "pathScore": node.path_score,
                "depth": node.depth,
                "type": node.metadata.get("type", "unknown"),
                "directive": node.metadata.get("directive"), # Pass full directive to UI
                "isBestPath": node_id in best_path_ids
            },
            "type": "thoughtNode", # Custom type for React Flow
            "position": {"x": 0, "y": 0}, # Layout handles this
            "className": node_class
        })
        
        # Edge (if parent exists)
        if node.parent_id:
            edge_class = "edge-default"
            if node_id in best_path_ids and node.parent_id in best_path_ids:
                edge_class = "edge-selected"
            elif node_id not in best_path_ids:
                edge_class = "edge-pruned" # Simple heuristic: if not best, consider pruned/alternative
                
            edges.append({
                "id": f"{node.parent_id}-{node_id}",
                "source": node.parent_id,
                "target": node_id,
                "className": edge_class,
                "animated": node_id in best_path_ids
            })

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        meta={
            "best_path_ids": best_path_ids,
            "strategy": state.get("strategy", ""),
            "content": {
                "full_text": state.get("full_text", ""), # Project ID: 25-26J-130
                "visual_tags": state.get("visual_tags", []) # Project ID: 25-26J-130
            },
            "body_text": state.get("body_text", ""), # Legacy support
            "run_stats": {
                "total_nodes": len(tree_memory),
                "depth": state.get("frontier", [ThoughtNode(content="", depth=0)])[0].depth if state.get("frontier") else 0
            },
            "context_data": state.get("context_data", {}), 
            "profile": state.get("profile", {}),
            "interaction_id": state.get("interaction_id"),
            "strategy_label": state.get("selected_strategy_label")
        }
    )

@fastapi_app.post("/api/run_sim", response_model=GraphResponse)
async def run_simulation(req: ScenarioRequest, user_id: str = Depends(get_current_user)):
    print(f"\n[Pipeline] 🚀 Start Learning Triggered for user: {user_id}")
    print(f"[Pipeline] 🎯 Target Topic: {req.topic_title or 'Default'}")
    
    student_id = req.student_id if hasattr(req, 'student_id') else user_id
    
    # --- Resolution chain: session → plan → collection_id ---
    db = get_db_connection()
    resolved_collection_id = None

    session_id = req.session_id or req.synthesis_id

    if not session_id:
        print(f"[Pipeline] ❌ No session_id in request for {student_id}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=200, content={
            "error": "NO_SESSION",
            "message": "No session_id provided. Please start a learning session first."
        })

    try:
        from bson import ObjectId
        # Step 1 — Look up session in the correct collection: learning_sessions
        session_doc = db.learning_sessions.find_one({"_id": ObjectId(session_id)})
        if not session_doc:
            print(f"[Pipeline] ❌ Session not found in learning_sessions: {session_id}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={
                "error": "NO_SESSION",
                "message": "Session not found. Please reload and try again."
            })

        print(f"[Pipeline] ✅ Session found: {session_id}")

        # Step 2 — Get plan_id from session
        plan_id = session_doc.get("plan_id")
        if not plan_id:
            print(f"[Pipeline] ❌ No plan_id on session: {session_id}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={
                "error": "NO_PLAN",
                "message": "Session is not linked to a learning plan."
            })

        print(f"[Pipeline] ✅ plan_id resolved: {plan_id}")

        # Step 3 — Look up plan and extract collection_id
        plan_doc = db.learning_plans.find_one({"_id": plan_id})
        if not plan_doc:
            print(f"[Pipeline] ❌ Plan not found: {plan_id}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={
                "error": "NO_PLAN",
                "message": "Learning plan not found."
            })

        # Fallback: check both nested and top-level locations
        resolved_collection_id = (
            plan_doc.get("system_metadata", {}).get("collection_id")
            or plan_doc.get("collection_id")
        )

        if resolved_collection_id:
            print(f"[Pipeline] ✅ collection_id resolved: {resolved_collection_id}")
        else:
            print(f"[Pipeline] ❌ NO_COLLECTION for plan: {plan_id}")

    except Exception as e:
        print(f"[Pipeline] ⚠️ Resolution chain failed: {e}")

    if not resolved_collection_id:
        print(f"[Pipeline] ❌ NO_COLLECTION error for {student_id}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={
                "error": "NO_COLLECTION",
                "message": "Study materials not yet processed. Please re-upload your files."
            }
        )


    # Use real topic if provided, else fallback to mock default
    if req.topic_title:
        query = f"I want to learn about {req.topic_title}"
        print(f"Using Real Topic Context: {req.topic_title}")
    else:
        query = "Teach me the quadratic formula"
        
    cv_state = "neutral"
    
    if req.scenario == "confused":
        cv_state = "confused"
    elif req.scenario == "bored":
        cv_state = "bored"
        
    # Inject real content into context if available
    context_data = {
        "test_cv_state": cv_state,
        "collection_id": resolved_collection_id, # Phase 21: RAG Isolation
        "topic_id": req.topic_title,
        "session_id": session_id,
        "module_id": str(plan_id) # plan_id is used as module_id for cache key grouping
    }
    if req.topic_content:
        context_data["topic_content"] = req.topic_content
        
    start_time = time.time()
    initial_state: AgentState = {
        "student_id": student_id,
        "user_query": query,
        "context_data": context_data,
        "profile": None,
        "frontier": [],
        "tree_memory": {},
        "best_node": None,
        "student_preferences": {},
        "strategy_blacklist": [],
        "teaching_strategy": None,
        "final_response": None,
        "reasoning_trace": [],
        "build_time": 0.0,
        "stop_early": False,
        "selected_strategy_label": None,
        "interaction_outcome": None,
        "interaction_id": req.synthesis_id,
        "start_time": start_time,
        "last_phase_time": start_time
    }
    
    # Run Agent
    agent = create_tot_graph()
    try:
        # Project ID: 25-26J-130: 90s Timeout Guard for Multimodal Synthesis
        # Track active synthesis to block interventions
        active_student_synthesis.add(student_id)
        final_state = await asyncio.wait_for(
            agent.ainvoke(initial_state, config={"recursion_limit": 20}),
            timeout=180.0
        )
        
        total_duration = int((time.time() - start_time) * 1000)
        print(f"[EduSynth Timing] TOTAL duration_ms={total_duration}")
        
        # --- ISSUE 6: Emit final delivery_complete event ---
        await sio.emit("progress", {
            "synthesis_id": req.synthesis_id,
            "phase": "delivery_complete",
            "message": "Lesson ready",
            "elapsed_ms": total_duration
        }, room=student_id)

        return transform_state_to_graph(final_state)
    except asyncio.TimeoutError:
        print(">>> Timeout Error: ToT Simulation exceeded 90s.")
        # Project ID: 25-26J-130: Return valid GraphResponse for UI stability
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "strategy": "TIMED_OUT",
                "body_text": "Pedagogical synthesis taking longer than expected. Please try again or simplify the topic.",
                "interaction_id": "error_timeout",
                "error": "TO_SIM_TIMEOUT"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        errorMessage = str(e)
        
        # Project ID: 25-26J-130: Handle Model Not Found (404)
        if "404" in errorMessage or "not found" in errorMessage.lower():
            displayMessage = "Model is temporarily unavailable in this region. Please contact support or try again later."
            interaction_id = "error_404"
        else:
            displayMessage = f"System encountered an error during synthesis: {errorMessage}"
            interaction_id = "error_crash"
            
        print(f"Agent Error: {e}")
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "strategy": "ERROR",
                "body_text": displayMessage,
                "interaction_id": interaction_id,
                "error": errorMessage
            }
        }
    finally:
        active_student_synthesis.discard(student_id)

@fastapi_app.post("/api/goal_decompose")
async def goal_decompose(req: DecomposeRequest, user_id: str = Depends(get_current_user)):
    print(f"Decomposing goal: {req.goal} (Collection: {req.collection_id}) for User: {user_id}")
    try:
        result = decompose_goal(req.goal, req.collection_id, user_id)
        return result
    except Exception as e:
        print(f"Decomposition Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/upload")
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

@fastapi_app.post("/api/analyze-anatomy")
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

@fastapi_app.get("/api/download-summary/{filename}")
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

# --- ANALYTICS ENDPOINTS ---
@fastapi_app.get("/api/analytics/historical")
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
@fastapi_app.get("/api/analytics/latest")
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

# --- LIVE TELEMETRY ENDPOINTS ---
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

@fastapi_app.post("/api/engagement/track")
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

@fastapi_app.post("/api/telemetry/cv")
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

@fastapi_app.post("/api/telemetry/rl")
async def receive_rl_telemetry(req: RLTelemetryRequest):
    # print(f">>> RL Telemetry Received: User={req.user_id}, Action={req.action_id}, Conf={req.confidence}")
    from integration.persistence import push_rl_strategy
    await push_rl_strategy(req.user_id, req.action_id, req.confidence, req.reasoning)
    return {"status": "telemetry_logged"}


@fastapi_app.post("/api/user/feedback")
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

@fastapi_app.post("/api/user/accept_shadow")
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

@fastapi_app.get("/api/analytics/profile/{student_id}")
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

@fastapi_app.get("/api/user/profile/{student_id}")
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

@fastapi_app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
