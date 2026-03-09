import asyncio
import json
import os
from dotenv import load_dotenv
from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState

load_dotenv()

async def verify_tot_logic():
    print("=== Agentic AI Core: ToT Logic Verification (Project ID: 25-26J-130) ===")
    
    # 1. Initialize State (Simulating server.py behavior)
    student_id = "test_student_001"
    query = "Explain the architecture of a Data Warehouse."
    
    initial_state = {
        "student_id": student_id,
        "user_query": query,
        "context_data": {}, # Will be populated by Node 1
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    # 2. Run Simulation
    agent = create_tot_graph()
    print(f"\n>>> Running Optimized ToT Simulation for: '{query}'")
    
    try:
        start_wall = time.time()
        final_state = await agent.ainvoke(initial_state, config={"recursion_limit": 20})
        end_wall = time.time()
        
        # 3. Analyze Results
        print("\n=== Verification Results ===")
        print(f"Total Wall Clock Time: {end_wall - start_wall:.2f}s")
        print(f"Internal Build Time Metric: {final_state.get('build_time', 0):.2f}s")
        
        # Check Pruning & Early Stopping
        if final_state.get("stop_early"):
            print("[✓] Early Stopping: Triggered successfully.")
        else:
            print("[!] Early Stopping: Not triggered (Score may be < 0.85).")
            
        # Check Branching (Beam Width should be 2)
        tree_mem = final_state["tree_memory"]
        depth_1_nodes = [n for n in tree_mem.values() if n.depth == 1]
        print(f"Beam Width Check: {len(depth_1_nodes)} nodes at Depth 1 (Limit: 2)")
        
        # Check Output
        best_node = final_state.get("best_node")
        if best_node:
            print(f"Final Path Score: {best_node.path_score:.2f}")
            print(f"Snippet: {best_node.content[:100]}...")
            
    except Exception as e:
        print(f"\n[!] Simulation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    asyncio.run(verify_tot_logic())
