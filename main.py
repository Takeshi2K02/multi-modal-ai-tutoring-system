import os
import sys
from dotenv import load_dotenv
from agent_core.graph import create_tot_graph

load_dotenv()

async def run_tot_demo():
    print("==================================================")
    print("      Agentic AI - Tree of Thought Planner        ")
    print("==================================================")
    
    app = create_tot_graph()
    
    student_id = "alex_123"
    query = "Teach me the quadratic formula"
    
    # --- Scenario 1: Confused ---
    print("\n\n>>> SCENARIO 1: Student is CONFUSED (Expect Breakdown/Explanation)")
    initial_state = {
        "student_id": student_id,
        "user_query": query,
        "context_data": {"test_cv_state": "confused"},
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    try:
        # Use recursion_limit to allow for depth
        result_1 = await app.ainvoke(initial_state, config={"recursion_limit": 20})
        print("\n[RESULT 1 Trace]")
        for trace in result_1.get("reasoning_trace", []):
            print(trace)
        print(f"\nFinal Response: {result_1.get('final_response')[:150]}...")
    except Exception as e:
        print(f"Error S1: {e}")

    # --- Scenario 2: Bored ---
    print("\n\n>>> SCENARIO 2: Student is BORED (Expect Gamification/Interaction)")
    initial_state_2 = {
        "student_id": student_id,
        "user_query": query,
        "context_data": {"test_cv_state": "bored"},
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    try:
        result_2 = await app.ainvoke(initial_state_2, config={"recursion_limit": 20})
        print("\n[RESULT 2 Trace]")
        for trace in result_2.get("reasoning_trace", []):
            print(trace)
        print(f"\nFinal Response: {result_2.get('final_response')[:150]}...")
    except Exception as e:
        print(f"Error S2: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_tot_demo())
