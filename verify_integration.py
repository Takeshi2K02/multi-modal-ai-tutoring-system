import asyncio
import json
from integration.persistence import push_cv_data, push_rl_strategy
from agent_core.graph import create_tot_graph
from agent_core.snapshot import get_student_snapshot

async def verify_integration():
    student_id = "test_student_001"
    
    print("\n--- Phase 1: Mocking Data Persistence ---")
    # Simulate CV data every 1.5s (we'll just push twice)
    # High score initially
    await push_cv_data(student_id, 0.9, "focused", gaze="forward", posture="upright", engagement_state="engaged")
    # Low score to trigger deviation alert (current < 50% of 0.9)
    await push_cv_data(student_id, 0.2, "frustrated", gaze="away", posture="slouched", engagement_state="disengaged")
    
    # Simulate RL strategy
    # Action ID 2 = Provide hint
    await push_rl_strategy(student_id, 2, 0.85, "Student needs scaffolding")
    print("Pushed CV and RL data to MongoDB.")

    print("\n--- Phase 2: Resolving Snapshot ---")
    snapshot = get_student_snapshot(student_id)
    print(f"Snapshot Resolved: {json.dumps(snapshot.dict(), indent=2)}")
    
    if snapshot.deviation_alert:
        print("✅ SUCCESS: Deviation Alert Triggered correctly.")
    else:
        print("❌ FAILURE: Deviation Alert not triggered.")

    print("\n--- Phase 3: Executing ToT Graph ---")
    graph = create_tot_graph()
    initial_state = {
        "student_id": student_id,
        "user_query": "Explain how a recursion works with a factorial example.",
        "frontier": [],
        "tree_memory": {},
        "reasoning_trace": []
    }
    
    print("Invoking Agentic AI Core...")
    result = await graph.ainvoke(initial_state)
    
    print("\n--- Verification Results ---")
    print(f"Final Response: {result['final_response']}")
    print("\nReasoning Trace:")
    for step in result['reasoning_trace']:
        print(f"  {step}")
        
    print("\nSnapshot used in context:")
    print(json.dumps(result['context_data']['snapshot'], indent=2))

if __name__ == "__main__":
    asyncio.run(verify_integration())
