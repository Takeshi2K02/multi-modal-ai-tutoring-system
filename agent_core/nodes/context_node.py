import redis
import json
import os
from datetime import datetime
from bson import ObjectId
from memory.student_memory import MemoryManager
from agent_core.schemas import AgentState, ThoughtNode
from agent_core.snapshot import get_student_snapshot
from services.vector_factory import get_vector_db
from db.connection import get_db_connection
from socket_manager import sio
import time

# Phase 1 Task 3: Redis Cache Initialization
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False
    print("[Pipeline] ⚠️ Redis unavailable — Falling back to direct Pinecone queries.")

async def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches context and initializes the tree root.
    Prioritizes RL 'teaching_strategy' if provided.
    """
    print("[ToT] 🧩 --- Node: Retrieve Context & Init Root ---")
    
    # --- RAG INTEGRATION (Phase 1 Task 3: Redis Caching) ---
    existing_context = state.get("context_data", {})
    topic_id = existing_context.get("topic_id")
    module_id = existing_context.get("module_id", "default_mod")
    student_id = state["student_id"]
    
    if REDIS_AVAILABLE and topic_id:
        cache_key = f"rag_cache:{module_id}:{topic_id}"
        try:
            t_start = time.time()
            cached_data = redis_client.get(cache_key)
            if cached_data:
                rag_results = json.loads(cached_data)
                t_end = time.time()
                cache_time_ms = (t_end - t_start) * 1000
                print(f"[Pipeline] ⚡ Redis Cache HIT for {cache_key} ({len(rag_results)} chunks) | IO time: {cache_time_ms:.2f}ms")
                
                # Fix: Fetch student snapshot even on cache hit (Not optional for downstream logic)
                memory = MemoryManager()
                profile = memory.get_student_profile(student_id)
                snapshot = get_student_snapshot(student_id)
                
                # Format RAG data for early return
                rag_context = "\n---\n".join([r["text"] for r in rag_results])
                rag_sources = [r.get("metadata", {}).get("source", "unknown") for r in rag_results]
                
                # Full state construction for early return
                context_data = {
                    **existing_context,
                    "rag_evidence": rag_context,
                    "rag_sources": rag_sources,
                    "snapshot": snapshot.dict()
                }
                
                root_node = ThoughtNode(depth=0, content=f"Root: Goal='{state['user_query']}'", score=1.0, path_score=1.0)
                interaction_id = state.get("interaction_id") or str(ObjectId())
                
                # Emit events for observability
                await sio.emit("tot_step", {
                    "step": "retrieve_context",
                    "snapshot": snapshot.dict(),
                    "student_id": student_id,
                    "query": state["user_query"]
                })
                
                await sio.emit("node_discovered", {
                    "synthesis_id": interaction_id,
                    "id": root_node.id,
                    "parent_id": None,
                    "depth": 0,
                    "content": root_node.content,
                    "metadata": {
                        **root_node.metadata,
                        "strategy_name": "Root Inquiry",
                        "internal_thought": "Initializing synthesis based on student profile (Cached).",
                        "pruning_status": "Active",
                        "localScore": root_node.score,
                        "pathScore": root_node.path_score
                    },
                    "rag_sources": rag_sources,
                    "timestamp": datetime.now().isoformat()
                })
                
                preferences = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
                blacklist = profile.get("strategy_blacklist", {}).get(state["user_query"], [])
                estimated_reading_time = profile.get("average_reading_speed", 120)

                # Fix 2: Fire timing log and return immediately
                print(f"[Cache] ✅ Chunks deserialized in {cache_time_ms:.2f}ms — returning early")
                from agent_core.timing_utils import log_and_emit_progress
                new_last_time = await log_and_emit_progress(state, "rag_complete", "Retrieving relevant content (Cached)")
                
                return {
                    **state,
                    "student_id": student_id,
                    "interaction_id": interaction_id,
                    "profile": profile,
                    "context_data": context_data,
                    "student_preferences": preferences,
                    "strategy_blacklist": blacklist,
                    "frontier": [root_node],
                    "tree_memory": {root_node.id: root_node},
                    "best_node": root_node,
                    "estimated_reading_time": estimated_reading_time,
                    "shadow_frontier": [],
                    "is_completed": False,
                    "build_time": time.time(),
                    "last_phase_time": new_last_time,
                    "stop_early": False
                }
        except Exception as e:
            print(f"[Pipeline] ⚠️ Redis Cache Error: {e}")

    # --- CACHE MISS PATH (Normal execution) ---
    memory = MemoryManager()
    profile = memory.get_student_profile(student_id)
    snapshot = get_student_snapshot(student_id)
    
    collection_id = existing_context.get("collection_id")
    rag_results = []
    
    print(f"[Pipeline] 🔍 Querying RAG Content Agent for: '{state['user_query']}'")
    # Fix 1: Move heavy import and initialization inside cache-miss path only
    from services.vector_factory import get_vector_db
    vectordb = get_vector_db()
    rag_filter = {"collection_id": collection_id} if collection_id else None
    
    # Phase 1 Task 3: Limit to top 5 for hot-path reasoning
    rag_results = vectordb.search(state["user_query"], top_k=5, filter=rag_filter)
    
    if not rag_results and rag_filter:
        print(f"[Pipeline] ⚠️ No results with filter. Falling back to global search.")
        rag_results = vectordb.search(state["user_query"], top_k=5, filter=None)
    
    print(f"[Pipeline] 📚 Retrieved {len(rag_results)} chunks from Pinecone")

    # Fix 1: Move secondary DB lookups for Mermaid inside cache-miss (Anything non-essential skipped on hit)
    mermaid_template = None
    if topic_id:
        try:
            db = get_db_connection()
            session_id = existing_context.get("session_id")
            if session_id:
                session = db.learning_sessions.find_one({"_id": ObjectId(session_id)})
                if session:
                    plan = db.learning_plans.find_one({"_id": session["plan_id"]})
                    if plan:
                        for lecture in plan.get("curriculum", {}).get("structure", []):
                            for topic in lecture.get("children", []):
                                if topic.get("title") == topic_id or topic.get("id") == topic_id:
                                    mermaid_template = topic.get("mermaid_template")
                                    if mermaid_template:
                                        print(f"[Pipeline] 🎨 Pre-built Mermaid found for topic: {topic_id}")
                                    break
                            if mermaid_template: break
        except Exception as e:
            print(f"[Pipeline] ⚠️ Mermaid Lookup Error: {e}")

    rag_context = "\n---\n".join([r["text"] for r in rag_results])
    rag_sources = [r.get("metadata", {}).get("source", "unknown") for r in rag_results]

    context_data = {
        **existing_context,
        "snapshot": existing_context.get("snapshot") or snapshot.dict(),
        "history": memory.get_recent_history(student_id),
        "rag_evidence": rag_context,
        "rag_sources": rag_sources,
        "prebuilt_mermaid": mermaid_template
    }

    # Initialize Root Node
    root_node = ThoughtNode(depth=0, content=f"Root: Goal='{state['user_query']}'", score=1.0, path_score=1.0)
    interaction_id = state.get("interaction_id") or str(ObjectId())
    
    await sio.emit("tot_step", {
        "step": "retrieve_context",
        "snapshot": snapshot.dict(),
        "student_id": student_id,
        "query": state["user_query"]
    })
    
    await sio.emit("node_discovered", {
        "synthesis_id": interaction_id,
        "id": root_node.id,
        "parent_id": None,
        "depth": 0,
        "content": root_node.content,
        "metadata": {
            **root_node.metadata,
            "strategy_name": "Root Inquiry",
            "internal_thought": "Initializing synthesis based on student profile and live CV state.",
            "pruning_status": "Active",
            "localScore": root_node.score,
            "pathScore": root_node.path_score
        },
        "rag_sources": rag_sources,
        "timestamp": datetime.now().isoformat()
    })
    
    preferences = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34}) if profile else {"visual": 0.33, "textual": 0.33, "interactive": 0.34}
    blacklist = profile.get("strategy_blacklist", {}).get(state["user_query"], []) if profile else []
    estimated_reading_time = profile.get("average_reading_speed", 120) if profile else 120

    from agent_core.timing_utils import log_and_emit_progress
    new_last_time = await log_and_emit_progress(state, "rag_complete", "Retrieving relevant content")

    return {
        **state,
        "student_id": student_id,
        "interaction_id": interaction_id,
        "profile": profile,
        "context_data": context_data,
        "student_preferences": preferences,
        "strategy_blacklist": blacklist,
        "frontier": [root_node],
        "tree_memory": {root_node.id: root_node},
        "best_node": root_node,
        "shadow_frontier": [],
        "is_completed": False,
        "estimated_reading_time": estimated_reading_time,
        "synthesis_locked": False,
        "handoff_buffer": [],
        "build_time": time.time(),
        "last_phase_time": new_last_time,
        "stop_early": False
    }
