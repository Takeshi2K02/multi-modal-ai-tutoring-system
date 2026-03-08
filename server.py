import sys
import os
from datetime import datetime, timedelta

# Add CV backend paths for direct hook access
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "cv", "backend"))

from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState, ThoughtNode
from services.decomposition_service import decompose_goal
from services.ingestion_service import ingest_document
from services.analysis_service import analyze_pdf_anatomy

from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI
fastapi_app = FastAPI()

# Socket.io Setup
sio = AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = ASGIApp(sio, fastapi_app)

# Helper to get sio instance (for other modules)
def get_sio():
    return sio

# Enable CORS for local dev
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.on_event("startup")
async def startup_event():
    print(">>> Agentic AI Core Starting...")
    print(f">>> VectorDB Provider: Local (ChromaDB at {os.getcwd()}/local_data)")
    print(">>> Mock VectorDB has been disabled.")

class ScenarioRequest(BaseModel):
    scenario: str # "confused" | "bored"
    topic_title: Optional[str] = None
    topic_content: Optional[str] = None

class DecomposeRequest(BaseModel):
    goal: str

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
            "timestamp": datetime.utcnow()
        }
        service.save_performance_record(record)
        service.update_session_progress(req.session_id, req.topic_id)
        
        return res_data
    except Exception as e:
        print(f"Challenge Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/learning_plan/save")
async def save_learning_plan(request: SavePlanRequest):
    try:
        service = LearningPlanService()
        plan_id = service.save_learning_plan(request.plan_data)
        return {"status": "success", "plan_id": plan_id}
    except Exception as e:
        print(f"Save Plan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/session/create")
async def create_session(request: CreateSessionRequest):
    print(f"Received Create Session Request: plan_id={request.plan_id}, student_id={request.student_id}")
    try:
        service = LearningSessionService()
        session_id = service.create_session(request.plan_id, request.student_id)
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
    return data

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
            "final_response": state.get("final_response", ""),
            "run_stats": {
                "total_nodes": len(tree_memory),
                "depth": state.get("frontier", [ThoughtNode(content="", depth=0)])[0].depth if state.get("frontier") else 0
            },
            "context_data": state.get("context_data", {}), # Expose CV/RL signals to UI
            "profile": state.get("profile", {}),
            "tie_break_trace": state.get("tie_break_trace")
        }
    )

@fastapi_app.post("/api/run_sim", response_model=GraphResponse)
async def run_simulation(req: ScenarioRequest):
    print(f"Running scenario: {req.scenario}")
    
    student_id = "alex_123"
    
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
    context_data = {"test_cv_state": cv_state}
    if req.topic_content:
        context_data["topic_content"] = req.topic_content
        
    initial_state = {
        "student_id": student_id,
        "user_query": query,
        "context_data": context_data,
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    # Run Agent
    agent = create_tot_graph()
    try:
        final_state = await agent.ainvoke(initial_state, config={"recursion_limit": 20})
        return transform_state_to_graph(final_state)
    except Exception as e:
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/goal_decompose")
async def goal_decompose(req: DecomposeRequest):
    print(f"Decomposing goal: {req.goal}")
    try:
        result = decompose_goal(req.goal)
        return result
    except Exception as e:
        print(f"Decomposition Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@fastapi_app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Ingests PDF, DOCX, PPTX, or TXT into the Local VectorDB.
    """
    print(f"Received upload: {file.filename}")
    try:
        allowed_extensions = {".pdf", ".docx", ".pptx", ".txt"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}. Allowed: {', '.join(allowed_extensions)}")
            
        content = await file.read()
        result = await ingest_document(content, file.filename)
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
async def get_historical_analytics(user_id: str = "alex_123"):
    """
    Fetches aggregated historical averages for CV and RL telemetry.
    """
    try:
        from agent_core.snapshot import _get_db
        from agent_core.schemas import RL_ACTION_MAP
        db = _get_db()
        
        # 1. CV Aggregation (Last 24 hours)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
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
async def get_latest_telemetry(user_id: str = "alex_123"):
    """
    Fetches the absolute latest CV and RL packets for the specified user.
    """
    try:
        from agent_core.snapshot import _get_db
        from agent_core.schemas import RL_ACTION_MAP
        db = _get_db()
        
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
    metadata: Optional[Dict] = None

class CVTrackRequest(BaseModel):
    frame: str
    user_id: str
    material_id: Optional[str] = None

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
        print(f">>> CV Frame Received. PID={os.getpid()} Exec={sys.executable}")
        print(f">>> Current sys.path: {sys.path[:3]}...") # Log start of path

        from services.engagement_service import process_engagement_data
        from integration.persistence import push_cv_data

        # Process via CV module services
        result = process_engagement_data(req.frame, material_id=req.material_id)
        
        # Persist and Emit (push_cv_data handles socket emission now)
        await push_cv_data(req.user_id, result['engagement_score'], result['emotion'], result)
        
        return result
    except Exception as e:
        print(f"Direct CV Hook Error: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@fastapi_app.post("/api/telemetry/cv")
async def receive_cv_telemetry(req: CVTelemetryRequest):
    print(f">>> CV Telemetry Received: User={req.user_id}, Score={req.engagement_score}, Emotion={req.emotion}")
    from integration.persistence import push_cv_data
    await push_cv_data(req.user_id, req.engagement_score, req.emotion, req.metadata)
    return {"status": "telemetry_logged"}

@fastapi_app.post("/api/telemetry/rl")
async def receive_rl_telemetry(req: RLTelemetryRequest):
    print(f">>> RL Telemetry Received: User={req.user_id}, Action={req.action_id}, Conf={req.confidence}")
    from integration.persistence import push_rl_strategy
    await push_rl_strategy(req.user_id, req.action_id, req.confidence, req.reasoning)
    return {"status": "telemetry_logged"}


@fastapi_app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
