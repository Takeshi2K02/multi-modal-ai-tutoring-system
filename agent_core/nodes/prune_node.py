from agent_core.schemas import AgentState
from agent_core.tot_config import CONFIG
from socket_manager import sio

async def prune_frontier(state: AgentState) -> AgentState:
    """
    Node 4: Selects the top K (Beam Width) nodes.
    """
    print(f"[ToT] ✂️ --- Node: Prune Frontier ---")
    frontier = state["frontier"]
    if not frontier:
        return state
        
    # Broadcast for UI Toast (Project ID: 25-26J-130)
    await sio.emit("tot_step", {
        "step": "PRUNING_FRONTIER",
        "message": f"Narrowing focus to top {CONFIG.beam_width} reasoning paths...",
        "synthesis_id": state.get("interaction_id")
    })
        
    # Standard beam search sorting by path_score
    # Tie-breaker: mastery_level from snapshot
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    mastery = snapshot.get("mastery_level", 0.5)
    
    sorted_frontier = sorted(frontier, key=lambda x: (x.path_score, mastery), reverse=True)
    beam = sorted_frontier[:CONFIG.beam_width]

    # Project ID: 25-26J-130: Real-time status propagation for intermediate nodes
    for node in sorted_frontier:
        status = "Beam" if node in beam and node.metadata.get("pruning_status") != "Selected" else \
                 "Selected" if node.metadata.get("pruning_status") == "Selected" else "Pruned"
        
        await sio.emit("node_discovered", {
            "synthesis_id": state.get("interaction_id"),
            "id": node.id,
            "metadata": {
                **node.metadata,
                "pruning_status": status,
                "localScore": node.score,
                "pathScore": node.path_score
            }
        })

    # Broadcast to Admin Dashboard
    await sio.emit("tot_step", {
        "step": "prune_frontier",
        "beam_size": len(beam)
    })
    
    from agent_core.timing_utils import log_and_emit_progress
    new_last_time = state.get("last_phase_time", state.get("start_time", 0))
    
    # Emit ToT complete if we reached the active max depth (depth 1 after Change 1)
    if beam and beam[0].depth >= 1:
        new_last_time = await log_and_emit_progress(state, "tot_complete", "Teaching strategy selected")

    return {**state, "frontier": beam, "last_phase_time": new_last_time}

def check_stop_condition(state: AgentState) -> str:
    """
    ToT stop condition & Selection Router.
    """
    is_done = False
    if state.get("stop_early"):
        print("[ToT] ⚡ >>> Terminating ToT Expansion: Early Stopping Flag Set")
        is_done = True

    frontier = state.get("frontier", [])
    if not frontier:
        is_done = True
    elif frontier and frontier[0].depth >= 1:
        # Change 1 (Project ID: 25-26J-130): Cap at Depth 1 to halve LLM calls.
        # Depth 0→1 completes one full expand+evaluate cycle; route immediately to finalize.
        print("[ToT] Max depth reached at Depth 1 — routing to finalize")
        is_done = True
    elif frontier and frontier[0].depth >= CONFIG.max_depth:
        # Original max_depth guard kept intact as a safety net.
        is_done = True

    if is_done:
        snapshot = state.get("context_data", {}).get("snapshot", {})
        if snapshot and snapshot.get("intervention_needed"):
            print("[Router] --- Diverting to Single Stream. Path: background_synthesis | Blocking Parallel State Update ---")
            return "shadow"
        else:
            print("[Router] --- Diverting to Single Stream. Path: finalize_output | Blocking Parallel State Update ---")
            return "finalize"

    return "expand"
