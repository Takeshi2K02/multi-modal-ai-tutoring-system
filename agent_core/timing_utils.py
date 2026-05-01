import time
from socket_manager import sio
from typing import Dict, Any

async def log_and_emit_progress(state: Dict[str, Any], phase: str, message: str):
    """
    Utility to record timing logs and emit WebSocket progress events.
    [EduSynth Timing] phase=<phase_name> duration_ms=<int> cumulative_ms=<int>
    """
    now = time.time()
    start_time = state.get("start_time", now)
    last_time = state.get("last_phase_time", start_time)
    
    duration_ms = int((now - last_time) * 1000)
    cumulative_ms = int((now - start_time) * 1000)
    
    # Log to terminal
    print(f"[EduSynth Timing] phase={phase} duration_ms={duration_ms} cumulative_ms={cumulative_ms}")
    
    # Emit progress via WebSocket
    # We use interaction_id as the room or identifier if needed
    student_id = state.get("student_id")
    if student_id:
        await sio.emit("progress", {
            "type": "progress",
            "phase": phase,
            "message": message,
            "elapsed_ms": cumulative_ms,
            "synthesis_id": state.get("interaction_id")
        }, room=student_id) # Emitting to student-specific room
    
    return now
