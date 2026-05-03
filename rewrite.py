import ast

def rewrite_server():
    with open("server.py", "r") as f:
        source = f.read()
        
    lines = source.splitlines()
    tree = ast.parse(source)
    
    # We want to KEEP:
    # Everything up to check_infrastructure, monitor_interventions, startup/shutdown, health_check, and the main block.
    # We ALSO want to KEEP the sio socket connection logic.
    # Everything else gets stripped and replaced by include_router calls.
    
    keep_names = {
        "cleanup_resources",
        "EndpointFilter",
        "connect",
        "handle_join_room",
        "check_infrastructure",
        "monitor_interventions",
        "startup_event",
        "shutdown_event",
        "health_check"
    }
    
    keep_types = {
        "Import",
        "ImportFrom",
    }
    
    # We will build a new file
    output = []
    
    # Let's manually compose server.py to guarantee correctness
    new_server = '''import sys
import os
import asyncio
import time
import warnings
import atexit
from datetime import datetime, timedelta
import logging

# Project ID: 25-26J-130: Clean Logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '3'
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = '1'
os.environ['TQDM_DISABLE'] = '1'

warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*ChatVertexAI.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

for logger_name in ["transformers", "mediapipe", "absl", "google", "google_auth_httplib2"]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

def cleanup_resources():
    """Project ID: 25-26J-130: Robust semaphore cleanup."""
    try:
        from multiprocessing import resource_tracker
        resource_tracker._resource_tracker._fd = None
        resource_tracker._resource_tracker.ensure_running()
    except Exception:
        pass

atexit.register(cleanup_resources)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "cv", "backend"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from socketio import ASGIApp
from jose import jwt

# Core auth & state
from core.auth import SECRET_KEY, ALGORITHM
from core.state import active_student_synthesis, triggered_interventions

# Initialize FastAPI
fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/api/engagement/track") == -1 and \\
               record.getMessage().find("/api/telemetry/rl") == -1 and \\
               record.getMessage().find("/api/analytics/latest") == -1 and \\
               record.getMessage().find("/socket.io/") == -1

logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

from socket_manager import sio, get_sio
app = ASGIApp(sio, fastapi_app)

@sio.event
async def connect(sid, environ, auth):
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get("token")
    if not token:
        auth_header = environ.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
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
        print(f"[Room] REJECTED: {sid} tried to join {requested_room}, authenticated as {authenticated_user_id}")
        return
    await sio.enter_room(sid, requested_room)
    print(f"[Room] {sid} joined room: {requested_room}")

from db.connection import get_db_connection
from services.vector_factory import get_vector_db

def check_infrastructure():
    print("\\n[Startup] 🩺 Running Infrastructure Health Check...")
    try:
        db = get_db_connection()
        print(f"[Startup] ✅ MongoDB Connected: {db.name}")
    except Exception as e:
        print(f"[Startup] ❌ MongoDB Connection Failed!")
        raise e
    try:
        vectordb = get_vector_db()
        print(f"[Startup] ✅ VectorDB Initialized ({type(vectordb).__name__})")
    except Exception as e:
        print(f"[Startup] ❌ VectorDB Initialization Failed!")
        raise e
    print("[Startup] 🚀 All systems green. Ready for requests.\\n")

check_infrastructure()

from agent_core.snapshot import get_student_snapshot
from agent_core.graph import create_tot_graph

async def monitor_interventions():
    print(">>> [Intervention] Proactive Monitor Started.")
    while True:
        try:
            db = get_db_connection()
            if db is None:
                await asyncio.sleep(10)
                continue
                
            latest_engagement = db.StudentEngagement.find_one(sort=[("timestamp", -1)])
            if not latest_engagement:
                await asyncio.sleep(10)
                continue
            
            student_id = latest_engagement.get("user_id")
            last_ping = latest_engagement.get("timestamp")
            
            if (datetime.now() - last_ping).total_seconds() > 30:
                await asyncio.sleep(10)
                continue

            if student_id in active_student_synthesis:
                await asyncio.sleep(10)
                continue

            snapshot = get_student_snapshot(student_id)
            
            if snapshot.intervention_needed:
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
                                await agent.ainvoke(initial_state)
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
            
        await asyncio.sleep(10)

@fastapi_app.on_event("startup")
async def startup_event():
    print(">>> Initializing Agentic AI Core...")
    asyncio.create_task(monitor_interventions())

@fastapi_app.on_event("shutdown")
async def shutdown_event():
    print(">>> Shutting down Agentic AI Core...")
    try:
        import multiprocessing.resource_tracker as rt
        rt._resource_tracker.ensure_running()
    except Exception as e:
        print(f"Cleanup warning: {e}")

@fastapi_app.get("/health")
def health_check():
    return {"status": "ok"}

# --- INCLUDE ROUTERS ---
from routers import auth, session, lessons, telemetry, users, monitor, upload
fastapi_app.include_router(auth.router)
fastapi_app.include_router(session.router)
fastapi_app.include_router(lessons.router)
fastapi_app.include_router(telemetry.router)
fastapi_app.include_router(users.router)
fastapi_app.include_router(monitor.router)
fastapi_app.include_router(upload.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
'''
    with open("server.py", "w") as f:
        f.write(new_server)
        
    # Also create routers/__init__.py
    open("routers/__init__.py", "w").close()

if __name__ == "__main__":
    rewrite_server()
