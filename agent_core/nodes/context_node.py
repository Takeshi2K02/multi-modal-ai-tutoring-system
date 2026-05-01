from datetime import datetime
from bson import ObjectId
from memory.student_memory import MemoryManager
from agent_core.schemas import AgentState, ThoughtNode
from agent_core.snapshot import get_student_snapshot
from services.vector_factory import get_vector_db
from socket_manager import sio
import time

async def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches context and initializes the tree root.
    Prioritizes RL 'teaching_strategy' if provided.
    """
    print("[ToT] 🧩 --- Node: Retrieve Context & Init Root ---")
    memory = MemoryManager()
    student_id = state["student_id"]
    
    profile = memory.get_student_profile(student_id)
    
    # --- TIME-SERIES SNAPSHOT INTEGRATION ---
    # Non-blocking lookup of latest CV/RL/Performance state
    snapshot = get_student_snapshot(student_id)
    
    # --- RAG INTEGRATION ---
    print(f"[Pipeline] 🔍 Querying RAG Content Agent for: '{state['user_query']}'")
    vectordb = get_vector_db()
    
    # Phase 21: RAG Isolation
    existing_context = state.get("context_data", {})
    collection_id = existing_context.get("collection_id")
    rag_filter = {"collection_id": collection_id} if collection_id else None
    
    rag_results = vectordb.search(state["user_query"], top_k=5, filter=rag_filter)
    
    # Fallback: If no results found with filter, try without filter (Global Search) (Project ID: 25-26J-130)
    if not rag_results and rag_filter:
        print(f"[Pipeline] ⚠️ No results with collection filter '{collection_id}'. Falling back to global search.")
        rag_results = vectordb.search(state["user_query"], top_k=5, filter=None)
    
    print(f"[Pipeline] 📚 Retrieved {len(rag_results)} chunks from ChromaDB")
    for i, res in enumerate(rag_results):
        snippet = res['text'][:60].replace('\n', ' ')
        print(f"   - Chunk {i+1}: {snippet}...")

    rag_context = "\n---\n".join([r["text"] for r in rag_results])
    rag_sources = [r.get("metadata", {}).get("source", "unknown") for r in rag_results]
    
    # Merge existing context data to preserve snapshot flags or collection ids
    context_data = {
        **existing_context,
        "snapshot": existing_context.get("snapshot") or snapshot.dict(),
        "history": memory.get_recent_history(student_id),
        "rag_evidence": rag_context,
        "rag_sources": rag_sources
    }

    # Initialize Root Node
    root_node = ThoughtNode(
        depth=0,
        content=f"Root: Goal='{state['user_query']}'",
        score=1.0,
        path_score=1.0,
    )
    
    # Generate Interaction ID early for real-time streaming (Project ID: 25-26J-130)
    interaction_id = state.get("interaction_id") or str(ObjectId())
    
    # Broadcast to Admin Dashboard
    await sio.emit("tot_step", {
        "step": "retrieve_context",
        "snapshot": snapshot.dict(),
        "student_id": student_id,
        "query": state["user_query"]
    })
    
    # --- REAL-TIME ToT EMISSION (Project ID: 25-26J-130) ---
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
    
    # Load Preferences & Blacklist (Project ID: 25-26J-130)
    preferences = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34}) if profile else {"visual": 0.33, "textual": 0.33, "interactive": 0.34}
    blacklist = profile.get("strategy_blacklist", {}).get(state["user_query"], []) if profile else []

    # Metadata Benchmarking (Project ID: 25-26J-130)
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
        "shadow_frontier": [], # Initialize shadow_frontier here
        "is_completed": False,
        "estimated_reading_time": estimated_reading_time,
        "synthesis_locked": False,
        "handoff_buffer": [],
        "build_time": time.time(),
        "last_phase_time": new_last_time,
        "stop_early": False
    }
