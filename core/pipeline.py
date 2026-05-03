import asyncio
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

async def run_simulation(req: ScenarioRequest, user_id: str, is_prefetch: bool = False):
    print(f"\n[Pipeline] 🚀 Start Learning Triggered for user: {user_id}")
    print(f"[Pipeline] 🎯 Target Topic: {req.topic_title or 'Default'}")
    
    student_id = req.student_id if req.student_id else user_id
    session_id = req.session_id or req.synthesis_id

    # Phase 2 Task 2: Check for Prefetched Result
    if not is_prefetch and session_id and req.topic_title:
        try:
            import redis, json
            r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
            prefetch_key = f"prefetch_tot:{session_id}:{req.topic_title}"
            cached_result = r.get(prefetch_key)
            
            if cached_result:
                payload = json.loads(cached_result)
                # Calculate age
                cached_time = datetime.fromisoformat(payload.get("timestamp", datetime.now().isoformat()))
                age = int((datetime.now() - cached_time).total_seconds())
                
                print(f"[Prefetch] ⚡ Serving prefetched ToT result for session={session_id} topic={req.topic_title} | age={age}s")
                
                # Fix: Frontend synthesis_complete handler expects 'full_text' key for rendering
                payload["full_text"] = payload.get("final_content")
                
                # Fix 1: Observability Log
                print(f"[Prefetch] 📤 Emitting payload keys: {list(payload.keys())}")
                
                # Emit immediately
                await sio.emit("synthesis_complete", payload)
                
                # Delete key after serving
                r.delete(prefetch_key)
                
                return GraphResponse(nodes=[], edges=[], meta={"prefetched": True})
            else:
                print(f"[Prefetch] ⏳ Prefetch not ready for session={session_id} — running pipeline live")
        except Exception as e:
            print(f"[Prefetch] ⚠️ Error during prefetch lookup: {e}")
            
    # Phase 3 Task 3: Persistent Content Retrieval (Issue 3)
    if not is_prefetch and session_id and req.topic_title:
        try:
            from services.learning_session_service import LearningSessionService
            service = LearningSessionService()
            saved_content = service.get_generated_content(student_id, req.topic_title)
            
            if saved_content:
                print(f"[Cache] ♻️ Serving saved synthesis for student={student_id} topic={req.topic_title}")
                # Construct a mock GraphResponse from saved content
                return {
                    "nodes": [],
                    "edges": [],
                    "meta": {
                        "from_cache": True,
                        "interaction_id": saved_content.get("interaction_id", "cached"),
                        "body_text": saved_content.get("content", {}).get("content", ""),
                        "strategy_label": "PREVIOUSLY_SAVED",
                        "content": saved_content.get("content", {})
                    }
                }
        except Exception as e:
            print(f"[Cache] ⚠️ Error during persistent lookup: {e}")

    # --- Resolution chain: session → plan → collection_id ---
    db = get_db_connection()
    resolved_collection_id = None

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



        # Step 2 — Get plan_id from session
        plan_id = session_doc.get("plan_id")
        if not plan_id:
            print(f"[Pipeline] ❌ No plan_id on session: {session_id}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=200, content={
                "error": "NO_PLAN",
                "message": "Session is not linked to a learning plan."
            })



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

        if not resolved_collection_id:
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
        "module_id": str(plan_id).strip() # plan_id is used as module_id for cache key grouping
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
        "last_phase_time": start_time,
        "is_prefetch": is_prefetch
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
        if not is_prefetch:
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
