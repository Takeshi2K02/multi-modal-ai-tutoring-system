import asyncio
import json
import os
from dotenv import load_dotenv
from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState

load_dotenv()

async def verify_tot_logic():
    print("=== Agentic AI Core: ToT Logic Verification ===")
    
    # 1. Define Dual Mock Inputs
    # RL Strategy from RL Engine
    mock_teaching_strategy = {
        "action_id": 2, # Provide Hint
        "reasoning": "Student has basic knowledge but is stuck on the step-by-step derivation.",
        "policy_name": "Provide hint"
    }
    
    # CV Data (Attention/Engagement)
    mock_cv_data = {
        "engagement_state": "confused",
        "engagement_score": 0.4,
        "attention_score": 0.6,
        "frustration_level": "high"
    }
    
    # 2. Initialize State
    initial_state = {
        "student_id": "test_student_001",
        "user_query": "Explain the concept of backpropagation in neural networks.",
        "teaching_strategy": mock_teaching_strategy,
        "context_data": {"test_cv_state": "confused", "cv": mock_cv_data},
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    print(f"\n[INPUT 1] RL Strategy: {mock_teaching_strategy['policy_name']}")
    print(f"[INPUT 2] CV State: {mock_cv_data['engagement_state']} (Frustration: {mock_cv_data['frustration_level']})")
    
    # 3. Run Simulation
    agent = create_tot_graph()
    print("\n>>> Running ToT Simulation (Gemini 2.5 Flash)...")
    
    try:
        final_state = await agent.ainvoke(initial_state, config={"recursion_limit": 20})
        
        # 4. Analyze Results
        print("\n=== Verification Results ===")
        
        # Check Input Consumption
        print(f"\n1. MOCK INPUT CONSUMPTION:")
        print(f"   - Processed RL Hint: {final_state['context_data']['rl_hint']['policy_name']}")
        print(f"   - Processed CV Signals: {final_state['context_data']['cv']['engagement_state']}")
        
        # Check Branching
        tree_mem = final_state["tree_memory"]
        depth_1_nodes = [n for n in tree_mem.values() if n.depth == 1]
        depth_2_nodes = [n for n in tree_mem.values() if n.depth == 2]
        
        print(f"\n2. BRANCHING LOGIC:")
        print(f"   - Depth 1 (Strategies): {len(depth_1_nodes)} branches generated.")
        for i, n in enumerate(depth_1_nodes):
            print(f"     [{i+1}] {n.content} (Score: {n.score:.2f})")
            
        print(f"   - Depth 2 (Delivery Paths): {len(depth_2_nodes)} variations generated.")

        # Check Selection Criteria
        best_node = final_state["best_node"]
        print(f"\n3. SELECTION CRITERIA:")
        print(f"   - Selected Path: {best_node.content}")
        print(f"   - Final Path Score: {best_node.path_score:.2f}")
        
        # 5. Full Trace for Proof
        print("\n=== THOUGHT TREE TRACE (ROOT -> BEST PATH) ===")
        for trace in final_state.get("reasoning_trace", []):
            print(f"   {trace}")
            
        # Write to report file
        with open("tot_verification_trace.txt", "w") as f:
            f.write("TOT VERIFICATION TRACE: GEMINI 2.5 FLASH\n")
            f.write("========================================\n\n")
            f.write(f"Inputs:\n- RL: {mock_teaching_strategy}\n- CV: {mock_cv_data}\n\n")
            f.write(f"Top Strategy selected: {final_state.get('selected_strategy_label')}\n")
            f.write("Full Reasoning Trace:\n")
            for trace in final_state.get("reasoning_trace", []):
                f.write(f"  {trace}\n")
            f.write("\nTree Statistics:\n")
            f.write(f"  Total Nodes: {len(tree_mem)}\n")
            f.write(f"  Branches at D1: {len(depth_1_nodes)}\n")

    except Exception as e:
        print(f"\n[!] Simulation Failed: {e}")
        if "403" in str(e) or "credentials" in str(e).lower():
            print("    HINT: Check if GOOGLE_APPLICATION_CREDENTIALS is set correctly and the JSON key exists.")

if __name__ == "__main__":
    asyncio.run(verify_tot_logic())
