import sys
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
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*inference_feedback_manager.*")
warnings.filterwarnings("ignore", message=".*landmark_projection_calculator.*")

for logger_name in ["transformers", "mediapipe", "absl", "google", "google_auth_httplib2", "tensorflow"]:
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
import core.state

# Initialize FastAPI
fastapi_app = FastAPI()

# Project ID: 25-26J-130: Log Deduplication State
_last_monitor_status = {} # student_id -> last_status_string
_busy_logged = False # Global flag for Rule 2

import redis
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project ID: 25-26J-130: Silence noisy backend logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GLOG_minloglevel'] = '2'

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return msg.find("/api/engagement/track") == -1 and \
               msg.find("/api/telemetry/rl") == -1 and \
               msg.find("/api/analytics/latest") == -1 and \
               msg.find("/api/analytics/historical") == -1 and \
               msg.find("/api/session/") == -1 and \
               msg.find("/api/prefetch/status") == -1 and \
               msg.find("/socket.io/") == -1

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

@sio.on("lesson_entered")
async def handle_lesson_entered(sid, data):
    student_id = data.get("student_id")
    topic_id = data.get("topic_id")
    core.state.active_lesson[student_id] = topic_id
    await sio.enter_room(sid, student_id)
    print(f"[Lesson] ✅ {student_id} joined room and entered: {topic_id}")

@sio.on("lesson_exited")
async def handle_lesson_exited(sid, data):
    student_id = data.get("student_id")
    core.state.active_lesson[student_id] = None
    await sio.leave_room(sid, student_id)
    print(f"[Lesson] 👋 {student_id} left room and exited lesson")

@sio.on("intervention_resolved")
async def on_intervention_resolved(sid, data):
    student_id = data.get("student_id")
    core.state.waiting_for_user_decision[student_id] = 0
    from agent_core.snapshot import reset_intervention_counter
    reset_intervention_counter()
    print(f">>> [Intervention] ✅ User resolved intervention for {student_id}")

from db.connection import get_db_connection
from services.vector_factory import get_vector_db

def check_infrastructure():
    print("\n[Startup] 🩺 Running Infrastructure Health Check...")
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
    print("[Startup] 🚀 All systems green. Ready for requests.\n")

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
                await asyncio.sleep(3)
                continue
            
            # Bug 2: Active Lesson Gate
            if core.state.active_lesson.get(student_id) is None:
                await asyncio.sleep(3)
                continue

            # Problem 3: Decision Window Timeout (60s)
            decision_timestamp = core.state.waiting_for_user_decision.get(student_id, 0)
            if decision_timestamp > 0 and (time.time() - decision_timestamp) > 60:
                print(f">>> [Intervention] ⏱️ User decision window timed out for {student_id}. Resetting to IDLE.")
                core.state.waiting_for_user_decision[student_id] = 0

            # Bug 3: Waiting for user decision gate
            if core.state.waiting_for_user_decision.get(student_id, 0) > 0:
                if _last_monitor_status.get(student_id) != "AWAITING":
                    print(f"🎯 [Intervention Check] student={student_id} | status=AWAITING_USER_DECISION — skipping")
                    _last_monitor_status[student_id] = "AWAITING"
                
                from agent_core.snapshot import reset_intervention_counter
                reset_intervention_counter(silent=True) 
                await asyncio.sleep(3)
                continue

            # Problem 5: Redis Shadow Lock Check
            lock_key = f"shadow_lock:{student_id}"
            if redis_client.exists(lock_key):
                if _last_monitor_status.get(student_id) != "LOCK":
                    print(f"🎯 [Intervention Check] student={student_id} | status=LOCKED (Redis) — skipping")
                    _last_monitor_status[student_id] = "LOCK"
                await asyncio.sleep(3)
                continue

            from core.state import is_tot_running
            if student_id in core.state.active_student_synthesis or is_tot_running:
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
                    
                    # Problem 1: Cooldown Registry Check
                    registry = core.state.triggered_interventions.get(inter_id, {"count": 0, "last_trigger": 0})
                    in_cooldown = (time.time() - registry["last_trigger"]) < 120
                    at_cap = registry["count"] >= 3

                    if at_cap:
                        if _last_monitor_status.get(student_id) != "CAP":
                            print(f"🎯 [Intervention Check] student={student_id} | status=CAP_REACHED (3/3) — skipping")
                            _last_monitor_status[student_id] = "CAP"
                        continue

                    if in_cooldown:
                        if _last_monitor_status.get(student_id) != "COOLDOWN":
                            print(f"🎯 [Intervention Check] student={student_id} | status=COOLDOWN — skipping")
                            _last_monitor_status[student_id] = "COOLDOWN"
                        continue
                        
                    if core.state.shadow_tot_in_progress:
                        # Rule 2: BUSY skipping
                        global _busy_logged
                        if not _busy_logged:
                            print(f"🎯 [Intervention Check] student={student_id} | status=BUSY (ToT in progress) — skipping")
                            _busy_logged = True
                            _last_monitor_status[student_id] = "BUSY"
                        
                        from agent_core.snapshot import reset_intervention_counter
                        reset_intervention_counter(silent=True) 
                        continue
                    else:
                        _busy_logged = False 
                        _last_monitor_status[student_id] = "IDLE"

                    print(f">>> [Intervention] 🛰️ Stagnation Detected for {inter_id}. (Trigger {registry['count']+1}/3)")
                    
                    # Problem 5: Set Redis Lock IMMEDIATELY
                    redis_client.setex(lock_key, 150, "locked")
                    
                    async def run_shadow_task():
                        try:
                            core.state.shadow_tot_in_progress = True
                            print(f">>> [Intervention] 🚀 Shadow ToT started for {student_id}")
                            
                            # Reset counter fresh for the new run
                            from agent_core.snapshot import reset_intervention_counter
                            reset_intervention_counter()
                            
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
                            # Bug 1: Safety Timeout (90s)
                            await asyncio.wait_for(agent.ainvoke(initial_state), timeout=90)
                            
                            # Problem 1: Increment Cooldown Registry on success
                            reg = core.state.triggered_interventions.get(inter_id, {"count": 0, "last_trigger": 0})
                            reg["count"] += 1
                            reg["last_trigger"] = time.time()
                            core.state.triggered_interventions[inter_id] = reg

                            # Problem 2: Fresh Interaction Anchor
                            new_inter_id = f"re-{int(time.time())}-{inter_id}"
                            db.interactions.insert_one({
                                "student_id": student_id,
                                "query": latest_inter["query"],
                                "timestamp": datetime.now(),
                                "parent_interaction_id": inter_id,
                                "re_intervention": True,
                                "is_stagnation_event": False # Fresh start
                            })
                            
                            # Problem 3: Mark Decision Timestamp
                            core.state.waiting_for_user_decision[student_id] = time.time()

                            # Project ID: 25-26J-130: Mark as stagnation event for analytics
                            db.interactions.update_one(
                                {"_id": latest_inter["_id"]},
                                {"$set": {"is_stagnation_event": True}}
                            )
                        except asyncio.TimeoutError:
                            print(">>> [Intervention] ⚠️ Shadow ToT timed out after 90s")
                        except Exception as e:
                            print(f">>> [Intervention] ❌ Shadow ToT failed: {e}")
                        finally:
                            core.state.shadow_tot_in_progress = False
                            global _busy_logged
                            _busy_logged = False 
                            # Problem 5: Cleanup Redis Lock
                            redis_client.delete(lock_key)
                            print(f">>> [Intervention] 🔓 Shadow ToT lock released for {student_id}")
                        
                    asyncio.create_task(run_shadow_task())

        except Exception as e:
            print(f">>> [Intervention] Monitor Error: {e}")
            
        await asyncio.sleep(3) # TEMP: testing only — revert before production # Production values: 10

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
