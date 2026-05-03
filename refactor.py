import ast
import os
from collections import defaultdict

# Mapping of function/class names to target modules
MAP = {
    # Auth
    "RegisterRequest": "routers/auth.py",
    "LoginRequest": "routers/auth.py",
    "register": "routers/auth.py",
    "login": "routers/auth.py",
    
    # Lessons
    "QuizSubmitRequest": "routers/lessons.py",
    "ChallengeRequest": "routers/lessons.py",
    "GeneratedContentRequest": "routers/lessons.py",
    "StudentProgressRequest": "routers/lessons.py",
    "PerformanceRecord": "routers/lessons.py",
    "submit_quiz": "routers/lessons.py",
    "save_performance": "routers/lessons.py",
    "get_lesson_content": "routers/lessons.py",
    "save_lesson_content": "routers/lessons.py",
    "sync_student_progress": "routers/lessons.py",
    "evaluate_challenge": "routers/lessons.py",
    
    # Session
    "SavePlanRequest": "routers/session.py",
    "CreateSessionRequest": "routers/session.py",
    "UpdateProgressRequest": "routers/session.py",
    "SessionStartRequest": "routers/session.py",
    "update_session_progress": "routers/session.py",
    "save_learning_plan": "routers/session.py",
    "create_session": "routers/session.py",
    "get_session": "routers/session.py",
    "manual_prefetch": "routers/session.py",
    "prefetch_status": "routers/session.py",
    "exit_session": "routers/session.py",
    "delete_session": "routers/session.py",
    "start_session_topic": "routers/session.py",
    "get_student_sessions": "routers/session.py",
    "trigger_background_tot": "routers/session.py",
    "prefetch_rag_to_redis": "routers/session.py",
    
    # Users
    "UserFeedbackRequest": "routers/users.py",
    "AcceptShadowRequest": "routers/users.py",
    "handle_user_feedback": "routers/users.py",
    "accept_shadow_intervention": "routers/users.py",
    "get_user_profile": "routers/users.py",
    
    # Telemetry
    "CVTelemetryRequest": "routers/telemetry.py",
    "CVTrackRequest": "routers/telemetry.py",
    "RLTelemetryRequest": "routers/telemetry.py",
    "track_engagement_direct": "routers/telemetry.py",
    "receive_cv_telemetry": "routers/telemetry.py",
    "receive_rl_telemetry": "routers/telemetry.py",
    
    # Monitor
    "get_historical_analytics": "routers/monitor.py",
    "get_latest_telemetry": "routers/monitor.py",
    "get_enhanced_analytics": "routers/monitor.py",
    
    # Upload
    "DecomposeRequest": "routers/upload.py",
    "goal_decompose": "routers/upload.py",
    "upload_file": "routers/upload.py",
    "analyze_anatomy": "routers/upload.py",
    "download_summary": "routers/upload.py",
    
    # Pipeline
    "transform_state_to_graph": "core/pipeline.py",
    "run_simulation": "core/pipeline.py",
}

IMPORTS = """import os
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
"""

PIPELINE_IMPORTS = """import asyncio
import time
import os
from datetime import datetime
from typing import Dict, Any, List

from socket_manager import sio
from db.connection import get_db_connection
from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState, ThoughtNode
from core.state import active_prefetch_tasks, active_student_synthesis, triggered_interventions
from core.schemas import ScenarioRequest, GraphResponse
"""

def extract_nodes(filepath):
    with open(filepath, 'r') as f:
        source = f.read()
    
    lines = source.splitlines()
    tree = ast.parse(source)
    
    nodes = []
    for node in tree.body:
        start = node.lineno - 1
        end = getattr(node, "end_lineno", node.lineno)
        if hasattr(node, "decorator_list") and node.decorator_list:
            start = node.decorator_list[0].lineno - 1
            
        nodes.append({
            "type": type(node).__name__,
            "name": getattr(node, "name", None),
            "start": start,
            "end": end,
            "node": node
        })
    return lines, nodes

def build():
    lines, nodes = extract_nodes("server.py")
    
    modules = defaultdict(list)
    for n in nodes:
        name = n["name"] if n["name"] else n["type"]
        if name in MAP:
            target = MAP[name]
            modules[target].append(n)
            
    # Write modules
    for target, mod_nodes in modules.items():
        os.makedirs(os.path.dirname(target), exist_ok=True)
        content = IMPORTS if target.startswith("routers") else PIPELINE_IMPORTS
        
        for n in sorted(mod_nodes, key=lambda x: x["start"]):
            chunk = "\n".join(lines[n["start"]:n["end"]])
            # Replace @fastapi_app.post -> @router.post, etc for routers
            if target.startswith("routers"):
                chunk = chunk.replace("@fastapi_app.", "@router.")
            content += "\n" + chunk + "\n"
            
        with open(target, "w") as f:
            f.write(content)
            
    print("Done generating modules.")

if __name__ == "__main__":
    build()
