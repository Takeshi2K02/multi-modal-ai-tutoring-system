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
from core.pipeline import run_simulation
from socket_manager import sio
from db.connection import get_db_connection, get_profiles_collection

# Services
from services.learning_plan_service import LearningPlanService
from services.learning_session_service import LearningSessionService

router = APIRouter()

class SavePlanRequest(BaseModel):
    plan_data: Dict[str, Any]

class CreateSessionRequest(BaseModel):
    plan_id: str
    student_id: str

class UpdateProgressRequest(BaseModel):
    session_id: str
    topic_id: str

class SessionStartRequest(BaseModel):
    session_id: str
    topic_id: str
    collection_id: Optional[str] = None

@router.post("/api/session/progress")
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

@router.post("/api/learning_plan/save")
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

@router.post("/api/session/create")
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

@router.get("/api/session/{session_id}")
async def get_session(session_id: str):
    service = LearningSessionService()
    data = service.get_session_details(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Phase 2 Task 1: Trigger Background ToT for first subtopic
    try:
        plan = data.get("plan", {})
        session_id_str = str(data.get("session", {}).get("_id"))
        student_id = data.get("session", {}).get("student_id")
        collection_id = plan.get("system_metadata", {}).get("collection_id")
        
        # Get first uncompleted subtopic
        structure = plan.get("curriculum", {}).get("structure", [])
        completed_topics = data.get("session", {}).get("progress", {}).get("completed_topics", [])
        
        target_topic = None
        for lecture in structure:
            for topic in lecture.get("children", []):
                if topic.get("title") not in completed_topics:
                    target_topic = topic.get("title")
                    break
            if target_topic:
                break
                
        if target_topic and session_id_str and student_id:
            # Fix 1: Synchronous Deduplication Guard (Refined)
            import redis
            r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
            lock_key = f"prefetch_tot_lock:{session_id_str}:{target_topic}"
            result_key = f"prefetch_tot:{session_id_str}:{target_topic}"
            task_key = f"{session_id_str}:{target_topic}"
            
            lock_exists = r.exists(lock_key)
            result_exists = r.exists(result_key)

            if lock_exists and result_exists:
                remaining_ttl = r.ttl(result_key)
                max_ttl = 1800 # 30 min as set in finalize_node.py
                age_seconds = max_ttl - remaining_ttl
                
                if age_seconds > 300:
                    print(f"[Prefetch] 🔄 Stale result detected (age={age_seconds}s) — invalidating and re-triggering for session={session_id_str}")
                    r.delete(lock_key, result_key)
                else:
                    print(f"[Prefetch] ⏭️ Fresh result cached for session={session_id_str} (age={age_seconds}s) — skipping")
                    raise StopIteration
            
            elif lock_exists and not result_exists:
                if task_key not in active_prefetch_tasks:
                    print(f"[Prefetch] 🔄 Stale lock detected (no task running) — deleting lock and re-triggering for session={session_id_str}")
                    r.delete(lock_key)
                else:
                    print(f"[Prefetch] ⏳ Background ToT in progress for session={session_id_str} — skipping")
                    raise StopIteration

            print(f"[Prefetch] 🚀 Background ToT started for session={session_id_str} topic={target_topic}")
            r.setex(lock_key, 2100, "locked") # 35 min TTL
            active_prefetch_tasks.add(task_key)
            asyncio.create_task(trigger_background_tot(
                student_id=student_id,
                session_id=session_id_str,
                topic_id=target_topic,
                collection_id=collection_id
            ))
    except StopIteration:
        pass
    except Exception as e:
        print(f"[Prefetch] ⚠️ Failed to trigger initial ToT: {e}")

    # Phase 1 Task 3: Trigger Background RAG Pre-fetch
    try:
        plan = data.get("plan", {})
        plan_id = str(plan.get("_id"))
        collection_id = plan.get("system_metadata", {}).get("collection_id")
        if collection_id and plan_id:
            plan_id = plan_id.strip()
            # Fix 4: Deduplication guard using Redis
            import redis
            try:
                r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0, socket_timeout=1)
                lock_key = f"prefetch_lock:{plan_id}"
                lock_exists = r.exists(lock_key)
                
                if lock_exists:
                    pass
                else:
                    # Verified: 2100s = 35 minutes TTL
                    r.setex(lock_key, 2100, "locked")
                    # We pre-fetch for all topics in the plan
                    topics = []
                    for lecture in plan.get("curriculum", {}).get("structure", []):
                        for topic in lecture.get("children", []):
                            topics.append(topic.get("title"))
                    
                    asyncio.create_task(prefetch_rag_to_redis(collection_id, topics, plan_id))
            except (redis.ConnectionError, redis.TimeoutError):
                print(f"[Cache] ⚠️ Redis down at pre-fetch time — chunks will be fetched live")
    except Exception as e:
        print(f"[Cache] Pre-fetch trigger failed: {e}")

    return data

@router.post("/api/prefetch")
async def manual_prefetch(req: Dict[str, str]):
    """
    Phase 2 Task 4: Manual prefetch trigger for next topic.
    """
    session_id = req.get("session_id")
    topic_id = req.get("topic_id") or req.get("topic_title")
    student_id = req.get("student_id") # Optional, fallback to session lookup if needed
    
    if not session_id or not topic_id:
        raise HTTPException(status_code=400, detail="session_id and topic_id/topic_title required")
    
    print(f"[Prefetch] 🔄 Manual prefetch triggered for next topic={topic_id}")
    
    # Resolve collection_id if not provided
    collection_id = req.get("collection_id")
    if not collection_id:
        db = get_db_connection()
        from bson import ObjectId
        session_doc = db.learning_sessions.find_one({"_id": ObjectId(session_id)})
        if session_doc:
            plan_doc = db.learning_plans.find_one({"_id": session_doc.get("plan_id")})
            if plan_doc:
                collection_id = plan_doc.get("system_metadata", {}).get("collection_id") or plan_doc.get("collection_id")
    
    # Fix 1: Synchronous Deduplication Guard (Refined)
    import redis
    r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
    lock_key = f"prefetch_tot_lock:{session_id}:{topic_id}"
    result_key = f"prefetch_tot:{session_id}:{topic_id}"
    
    lock_exists = r.exists(lock_key)
    result_exists = r.exists(result_key)
    task_key = f"{session_id}:{topic_id}"

    if lock_exists and result_exists:
        print(f"[Prefetch] ⏭️ Result already cached for session={session_id} — skipping")
        return {"status": "Already cached"}
        
    elif lock_exists and not result_exists:
        if task_key not in active_prefetch_tasks:
            print(f"[Prefetch] 🔄 Stale lock detected (no task running) — deleting lock and re-triggering for session={session_id}")
            r.delete(lock_key)
        else:
            print(f"[Prefetch] ⏳ Background ToT in progress for session={session_id} — skipping")
            return {"status": "In progress"}

    print(f"[Prefetch] 🚀 Background ToT started for session={session_id} topic={topic_id}")
    r.setex(lock_key, 2100, "locked") # 35 min TTL
    active_prefetch_tasks.add(task_key)
    asyncio.create_task(trigger_background_tot(
        student_id=student_id or "prefetch_user",
        session_id=session_id,
        topic_id=topic_id,
        collection_id=collection_id
    ))
    
    return {"status": "Prefetch started"}

async def trigger_background_tot(student_id: str, session_id: str, topic_id: str, collection_id: str):
    """
    Helper to run ToT in background and store in Redis.
    """
    task_key = f"{session_id}:{topic_id}"
    try:
        print(f"[Prefetch] 🚀 Background ToT task initiated for session={session_id} topic={topic_id}")
        start_time = time.time()
        
        # Reuse run_simulation logic by constructing a request
        req = ScenarioRequest(
            scenario="confused",
            topic_title=topic_id,
            synthesis_id=f"syn-{int(time.time()*1000)}", # Temporary ID for trace
            collection_id=collection_id,
            session_id=session_id,
            student_id=student_id
        )
        
        # We need to pass a flag to tell the graph it's a prefetch
        # I'll modify run_simulation to accept an is_prefetch flag or handle it via a wrapper
        await run_simulation(req, user_id=student_id, is_prefetch=True)
        
        duration = int((time.time() - start_time) * 1000)
        print(f"[Prefetch] ✅ Background ToT complete for session={session_id} | stored in Redis | duration={duration}ms")
        
    except Exception as e:
        print(f"[Prefetch] ⚠️ Background ToT failed for session={session_id}: {e}")
    finally:
        active_prefetch_tasks.discard(task_key)

@router.get("/api/prefetch/status")
async def prefetch_status(session_id: str, topic_id: str):
    """
    Lightweight endpoint for the frontend to poll ToT prefetch readiness.
    """
    try:
        import redis
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
        result_key = f"prefetch_tot:{session_id}:{topic_id}"
        
        ttl = r.ttl(result_key)
        
        # Redis ttl returns -1 if key exists but has no expiry, -2 if key doesn't exist
        if ttl > 0 or ttl == -1:
            max_ttl = 1800
            age = max_ttl - ttl if ttl > 0 else 0
            return {"ready": True, "age_seconds": age}
        else:
            return {"ready": False, "age_seconds": 0}
            
    except Exception as e:
        print(f"[Prefetch] ⚠️ Status check failed: {e}")
        return {"ready": False, "age_seconds": 0}

@router.post("/api/session/exit")
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
        print(f"[Cache] 🔌 Redis Connected (Write Path) | Host: {os.getenv('REDIS_HOST', 'localhost')} | DB: 0")
        from services.vector_factory import get_vector_db
        vectordb = get_vector_db()
        
        for topic in topics:
            # Fix 4: Normalize key with strip() to prevent mismatches
            cache_key = f"rag_cache:{plan_id.strip()}:{topic.strip()}"
            # Check if already cached
            if r.exists(cache_key): continue
            
            print(f"[Cache] 🛰️ Pre-fetching RAG for topic: {topic}")
            # Cap at 20 chunks as requested
            results = vectordb.search(f"Teach me about {topic}", top_k=20, filter={"collection_id": collection_id})
            if results:
                r.setex(cache_key, 1800, json.dumps(results)) # 30 min TTL
                print(f"[Cache] 📝 Writing key: {cache_key}")
        print(f"[Cache] ✅ Pre-fetch complete for plan {plan_id}")
    except Exception as e:
        print(f"[Cache] ⚠️ Background pre-fetch failed: {e}")

@router.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a learning session.
    """
    service = LearningSessionService()
    success = service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    return {"message": "Session deleted successfully"}

@router.post("/api/session/start")
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

@router.get("/api/sessions/student/{student_id}")
async def get_student_sessions(student_id: str):
    try:
        service = LearningSessionService()
        sessions = service.get_sessions_by_student(student_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"List Sessions Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/run_sim", response_model=GraphResponse)
async def run_sim_endpoint(req: ScenarioRequest, user_id: str = Depends(get_current_user)):
    """
    Direct endpoint for running simulation, used by the frontend.
    """
    return await run_simulation(req, user_id=user_id)
