import os
import sys
from dotenv import load_dotenv
from agent_core.graph import create_agent_graph

load_dotenv()

def run_agent_demonstration():
    print("==================================================")
    print("      Agentic AI Tutoring Core - Starter Demo     ")
    print("==================================================")
    
    app = create_agent_graph()
    
    student_id = "alex_123"
    query = "Teach me the quadratic formula"
    
    # --- Scenario 1: Student is Confused ---
    print("\n\n>>> SCENARIO 1: Student is CONFUSED (Needs Breakdown/Explanation)")
    initial_state = {
        "student_id": student_id,
        "user_query": query,
        "context_data": {"test_cv_state": "confused"}, # Force 'confused' state
        "retries": 0,
        "candidate_strategies": [],
        "strategy_scores": {}
    }
    
    try:
        result_1 = app.invoke(initial_state)
        print("\n[RESULT 1]")
        print(f"Selected Strategy: {result_1.get('selected_strategy_label')}")
        print(f"Reasoning: {result_1.get('reasoning_trace')}")
        print(f"Response Preview: {result_1.get('final_response')[:100]}...")
    except Exception as e:
        print(f"Error in Scenario 1: {e}")

    # --- Scenario 2: Student is Bored ---
    print("\n\n>>> SCENARIO 2: Student is BORED (Needs Gamification/Interaction)")
    initial_state_2 = {
        "student_id": student_id,
        "user_query": query,
        "context_data": {"test_cv_state": "bored"}, # Force 'bored' state
        "retries": 0,
        "candidate_strategies": [],
        "strategy_scores": {}
    }
    
    try:
        result_2 = app.invoke(initial_state_2)
        print("\n[RESULT 2]")
        print(f"Selected Strategy: {result_2.get('selected_strategy_label')}")
        print(f"Reasoning: {result_2.get('reasoning_trace')}")
        print(f"Response Preview: {result_2.get('final_response')[:100]}...")
    except Exception as e:
        print(f"Error in Scenario 2: {e}")

if __name__ == "__main__":
    run_agent_demonstration()
