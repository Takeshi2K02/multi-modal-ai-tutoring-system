import os
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from memory.student_memory import MemoryManager
from mocks.data_generators import get_mock_cv_inputs, get_mock_rl_strategy
from db.schemas import AgentState

# Initialize LLM
# Note: Using a placeholder API key from the prompt if env var not set.
# In production, this should always be an env var.
api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyBu38SUXgGClP4PDZhn2pFRFBsPPB66D9A")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", google_api_key=api_key, temperature=0.7)

# --- Nodes ---

def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches student profile from memory and current mock inputs (CV, RL).
    """
    print("--- Node: Retrieve Context ---")
    memory = MemoryManager()
    student_id = state["student_id"]
    
    # Fetch Profile
    profile = memory.get_student_profile(student_id)
    
    # Fetch Mocks (simulate real-time sensor data)
    # We check if 'cv_state' was passed in state for testing, else default
    test_cv_state = state.get("context_data", {}).get("test_cv_state", "neutral")
    cv_data = get_mock_cv_inputs(state=test_cv_state)
    rl_strategy = get_mock_rl_strategy()
    
    context_data = {
        "cv": cv_data,
        "rl_hint": rl_strategy,
        "history": memory.get_recent_history(student_id)
    }
    
    return {**state, "profile": profile, "context_data": context_data}

def generate_strategies(state: AgentState) -> AgentState:
    """
    Node 2: Generates candidate teaching strategies based on context.
    """
    print(f"--- Node: Generate Strategies (Attempt {state.get('retries', 0) + 1}) ---")
    
    profile = state["profile"]
    context = state["context_data"]
    query = state["user_query"]
    
    prompt = PromptTemplate(
        template="""
        You are an expert AI tutor.
        Student Profile: {profile}
        Real-time Context (Engagement/Emotion): {cv_context}
        RL System Suggestion: {rl_hint}
        Student Goal/Query: {query}
        
        Generate 3 distinct teaching strategies to address the query.
        Consider the student's learning style, current engagement level, and the RL suggestion.
        
        Output valid JSON with the following structure:
        {{
            "strategies": [
                {{
                    "label": "Short name of strategy",
                    "description": "Description of how to apply it",
                    "content": "Draft of the actual explanation/response"
                }},
                ...
            ]
        }}
        """,
        input_variables=["profile", "cv_context", "rl_hint", "query"]
    )
    
    chain = prompt | llm | JsonOutputParser()
    
    try:
        result = chain.invoke({
            "profile": str(profile),
            "cv_context": str(context["cv"]),
            "rl_hint": context["rl_hint"],
            "query": query
        })
        strategies = result.get("strategies", [])
    except Exception as e:
        print(f"Error generating strategies: {e}")
        strategies = []

    # Store full strategy objects locally, put simple list in state if needed, 
    # but AgentState defines candiate_strategies as List[str]. 
    # Let's adjust to store the dicts in a temp way or just serialized strings.
    # For simplicity, we'll store the list of dicts in 'candidate_strategies' (AgentState definition allows loose typing at runtime or we update schema).
    # The schema said List[str], let's try to stick to that or update schema. 
    # Validating schema: candidate_strategies: List[str]. 
    # Let's serialize them for now to be safe, or just store labels.
    # Actually, we need the content for the final output. 
    # I will store them as a list of dicts. Python TypedDict doesn't enforce runtime checks so it's fine.
    
    return {**state, "candidate_strategies": strategies}

def evaluate_strategies(state: AgentState) -> AgentState:
    """
    Node 3: Scores the generated strategies.
    """
    print("--- Node: Evaluate Strategies ---")
    strategies = state["candidate_strategies"]
    profile = state["profile"]
    context = state["context_data"]
    
    if not strategies:
        return {**state, "strategy_scores": {}}

    prompt = PromptTemplate(
        template="""
        Evaluate these teaching strategies for student: {profile}
        Context: {cv_context}
        
        Strategies: {strategies}
        
        Score each strategy from 0.0 to 1.0 based on:
        1. Relevance to learning style
        2. Appropriateness for engagement level (e.g. if bored, needs high interactivity)
        3. Clarity and correctness
        
        Output valid JSON:
        {{
            "scores": {{
                "strategy_label_1": 0.8,
                "strategy_label_2": 0.5,
                ...
            }}
        }}
        """,
        input_variables=["profile", "cv_context", "strategies"]
    )
    
    chain = prompt | llm | JsonOutputParser()
    
    try:
        result = chain.invoke({
            "profile": str(profile),
            "cv_context": str(context["cv"]),
            "strategies": str(strategies)
        })
        scores = result.get("scores", {})
    except Exception as e:
        print(f"Error evaluating strategies: {e}")
        scores = {}
        
    return {**state, "strategy_scores": scores}

def select_strategy_node(state: AgentState) -> AgentState:
    """
    Node 4 (Logic): Selects the best strategy based on scores.
    Sets 'selected_strategy_label' and 'final_response'.
    """
    print("--- Node: Selection Logic ---")
    scores = state["strategy_scores"]
    strategies = state["candidate_strategies"]
    
    if not scores or not strategies:
        return state

    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]
    
    # Find the full strategy object
    selected_strat = next((s for s in strategies if s["label"] == best_label), None)
    
    if selected_strat:
        return {
            **state,
            "selected_strategy_label": best_label,
            "final_response": selected_strat["content"],
            "reasoning_trace": [f"Selected {best_label} with score {best_score}"]
        }
    
    return state

def format_output(state: AgentState) -> AgentState:
    """
    Node 5: Final formatting.
    """
    print("--- Node: Final Output ---")
    # You could do post-processing here.
    # For now, we just pass through, maybe log to DB.
    
    memory = MemoryManager()
    memory.save_interaction({
        "student_id": state["student_id"],
        "goal_id": "goal_1", # placeholder
        "chosen_strategy": state["selected_strategy_label"],
        "scores": state["strategy_scores"],
        "cv_state": state["context_data"]["cv"]["emotion"],
        "rl_hint": state["context_data"]["rl_hint"],
        "response_text": state["final_response"]
    })
    
    return state

# --- Conditional Logic ---

def check_score_threshold(state: AgentState) -> str:
    """
    Determines if we should loop back or proceed.
    Threshold = 0.8
    Max Retries = 3 (default 0 start, so 0,1,2 = 3 attempts)
    """
    if not scores:
        if retries < 2:
            return "retry"
        return "finalize" # Give up after max retries
        
    best_score = max(scores.values())
    retries = state.get("retries", 0)
    
    print(f"--- Check: Best score {best_score}, Retries {retries} ---")
    
    if best_score >= 0.8:
        return "finalize"
    
    if retries < 2: # Allow 2 retries (3 total attempts)
        return "retry"
        
    return "finalize" # Max retries reached, accept best so far

def retry_logic(state: AgentState) -> AgentState:
    """
    Updates retry count.
    """
    return {**state, "retries": state.get("retries", 0) + 1}

# --- Graph Definition ---

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_strategies", generate_strategies)
    workflow.add_node("evaluate_strategies", evaluate_strategies)
    workflow.add_node("select_strategy_node", select_strategy_node) # Part of decision process
    workflow.add_node("retry_node", retry_logic)
    workflow.add_node("format_output", format_output)
    
    # Set Entry Point
    workflow.set_entry_point("retrieve_context")
    
    # Add Edges
    workflow.add_edge("retrieve_context", "generate_strategies")
    workflow.add_edge("generate_strategies", "evaluate_strategies")
    workflow.add_edge("evaluate_strategies", "select_strategy_node")
    
    # Conditional Edge
    workflow.add_conditional_edges(
        "select_strategy_node",
        check_score_threshold,
        {
            "finalize": "format_output",
            "retry": "retry_node"
        }
    )
    
    workflow.add_edge("retry_node", "generate_strategies")
    workflow.add_edge("format_output", END)
    
    return workflow.compile()
