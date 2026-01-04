import os
import uuid
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from memory.student_memory import MemoryManager
from mocks.data_generators import get_mock_cv_inputs, get_mock_rl_strategy
from agent_core.schemas import AgentState, ThoughtNode, ToTConfig
from agent_core.llm import get_llm

# Configuration
CONFIG = ToTConfig(
    max_depth=2,
    beam_width=2,
    branching_factor=3,
    score_threshold=0.85
)

# Initialize LLM
# Initialize LLM
llm = get_llm()

# --- Nodes ---

def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches context and initializes the tree root.
    """
    print("--- Node: Retrieve Context & Init Root ---")
    memory = MemoryManager()
    student_id = state["student_id"]
    
    profile = memory.get_student_profile(student_id)
    
    # Mocks
    test_cv_state = state.get("context_data", {}).get("test_cv_state", "neutral")
    cv_data = get_mock_cv_inputs(state=test_cv_state)
    rl_strategy = get_mock_rl_strategy() # Returns Dict with action_id, reasoning, etc.
    
    context_data = {
        "cv": cv_data,
        "rl_hint": rl_strategy,
        "history": memory.get_recent_history(student_id)
    }

    # Initialize Root Node
    root_node = ThoughtNode(
        depth=0,
        content=f"Root: Goal='{state['user_query']}'",
        score=1.0,
        path_score=1.0,
        metadata={"type": "root"}
    )
    
    return {
        **state,
        "profile": profile,
        "context_data": context_data,
        "frontier": [root_node],
        "tree_memory": {root_node.id: root_node},
        "best_node": root_node
    }

def expand_frontier(state: AgentState) -> AgentState:
    """
    Node 2: Expands the current frontier by generating thoughts.
    Depth 0->1: Strategies
    Depth 1->2: Substeps/Content
    """
    frontier = state["frontier"]
    if not frontier:
        return state # Should be caught by stop condition, but safety check

    current_depth = frontier[0].depth
    next_depth = current_depth + 1
    
    print(f"--- Node: Expand Frontier (Depth {current_depth} -> {next_depth}) ---")
    
    new_frontier = []
    tree_memory = state["tree_memory"].copy()
    
    for node in frontier:
        # Generate children for this node
        children_contents = _generate_children_content(state, node, next_depth)
        
        for content in children_contents:
            child = ThoughtNode(
                parent_id=node.id,
                depth=next_depth,
                content=content["content"],
                metadata=content.get("metadata", {})
            )
            # Add to local tracking
            new_frontier.append(child)
            tree_memory[child.id] = child
            
    return {**state, "frontier": new_frontier, "tree_memory": tree_memory}

def _generate_children_content(state: AgentState, parent_node: ThoughtNode, target_depth: int) -> List[Dict]:
    """
    Helper to generate content based on depth.
    """
    profile = state["profile"]
    context = state["context_data"]
    query = state["user_query"]
    
    import time
    import json

    max_retries = 3
    base_delay = 5

    if target_depth == 1:
        # Generate Strategies
        prompt = PromptTemplate(
            template="""
            Role: You are a strict JSON data generator. You do not speak or explain.
            
            Student: {profile}
            
            REAL-TIME SIGNALS:
            CV Data: {cv}
            RL Policy: {rl}
            
            Goal: {query}
            
            TASK: Generate {k} teaching strategies based on signals.
            
            OUTPUT RULES:
            1. Return ONLY valid JSON.
            2. NO introductory text (e.g. "Here returns...").
            3. NO markdown blocks (```json).
            4. Start output immediately with {{.
            
            JSON FORMAT:
            {{ "options": [ {{ "label": "Strategy Name", "approach": "Description" }}, ... ] }}
            """,
            input_variables=["profile", "cv", "rl", "query", "k"]
        )
        
        for attempt in range(max_retries):
            try:
                chain = prompt | llm | JsonOutputParser()
                res = chain.invoke({
                    "profile": str(profile), 
                    "cv": json.dumps(context["cv"], ensure_ascii=False), 
                    "rl": json.dumps(context["rl_hint"], ensure_ascii=False),
                    "query": query, "k": CONFIG.branching_factor
                })
                # ROBUST PARSING: Handle if LLM returns a List directly instead of {"options": [...]}
                options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                return [{"content": opt["label"], "metadata": {"approach": opt.get("approach", ""), "type": "strategy"}} for opt in options]
            except Exception as e:
                print(f"Gen D1 Attempt {attempt+1} Failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (attempt + 1))
                else:
                    raise e



    elif target_depth == 2:
        # Generate Substeps / Content for the Strategy
        prompt = PromptTemplate(
            template="""
            Role: You are a strict JSON data generator. You do not speak.
            
            Student: {profile}
            Context: {cv}
            Strategy: {strategy} ({approach})
            Goal: {query}
            
            TASK: Generate {k} variations of explanation.
            
            OUTPUT RULES:
            1. Return ONLY valid JSON.
            2. NO introductory text.
            3. Start output immediately with {{.
            
            JSON FORMAT: 
            {{ "options": [ {{ "text": "Explanation content...", "focus": "Main focus" }}, ... ] }}
            """,
            input_variables=["profile", "cv", "strategy", "approach", "query", "k"]
        )
        for attempt in range(max_retries):
            try:
                chain = prompt | llm | JsonOutputParser()
                parent_approach = parent_node.metadata.get("approach", "")
                res = chain.invoke({
                    "profile": str(profile), 
                    "cv": json.dumps(context["cv"], ensure_ascii=False), 
                    "strategy": parent_node.content, "approach": parent_approach,
                    "query": query, "k": CONFIG.branching_factor
                })
                # ROBUST PARSING: Handle if LLM returns a List directly instead of {"options": [...]}
                options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                return [{"content": opt["text"], "metadata": {"focus": opt.get("focus", ""), "type": "response"}} for opt in options]
            except Exception as e:
                 print(f"Gen D2 Attempt {attempt+1} Failed: {e}")
                 if attempt < max_retries - 1:
                    time.sleep(base_delay * (attempt + 1))
                 else:
                    raise e

             
    return []

def evaluate_frontier(state: AgentState) -> AgentState:
    """
    Node 3: Scores the new nodes in the frontier.
    Calculates Path Score.
    """
    print("--- Node: Evaluate Frontier ---")
    frontier = state["frontier"]
    tree_memory = state["tree_memory"]
    
    if not frontier:
        return state

    # Batch evaluate or loop (loop implies more LLM calls, batch is better)
    # For simplicity in this POC, we'll evaluate in one prompt if possible, or loop.
    # Evaluating a list of thoughts is easier.
    
    # We need to construct a robust prompt that sees the item + parent context
    # Scoring: 0.0 to 1.0. 
    # Path Score = Average(Node Score, Parent Path Score) OR Product.
    # Let's use Simple Average for stability in POC: (ParentPathScore + LocalScore) / 2
    
    scored_frontier = []
    
    for node in frontier:
        local_score = _score_node_content(state, node, tree_memory)
        parent = tree_memory.get(node.parent_id)
        parent_path_score = parent.path_score if parent else 1.0
        
        # Path accumulation logic: decay slightly to penalize depth, or avg.
        # Let's do Average to keep it balanced.
        if node.depth == 1:
            path_score = local_score # Strategy selection is critical
        else:
            path_score = (parent_path_score + local_score) / 2
            
        node.score = local_score
        node.path_score = path_score
        scored_frontier.append(node)
        
    # Update Best Node
    # Logic Update: Always update to the best of the CURRENT frontier (deeper) 
    # so we track the path to the leaf, even if score decays from 1.0 (Root).
    current_best = state["best_node"]
    frontier_best = max(scored_frontier, key=lambda x: x.path_score) if scored_frontier else None
    
    if frontier_best:
        current_best = frontier_best

    return {**state, "frontier": scored_frontier, "best_node": current_best}

def _score_node_content(state: AgentState, node: ThoughtNode, tree_memory: Dict[str, ThoughtNode]) -> float:
    # Use LLM to score relevance
    prompt = PromptTemplate(
        template="""
        Role: You are a strict scoring engine.
        
        Goal: {query}
        Evaluator Data: {cv}
        Student: {profile}
        
        Candidate: "{content}"
        
        CRITERIA:
        1. Context Match (Confused -> Scaffolded? Bored -> Fun?)
        2. RL Alignment
        
        OUTPUT RULES:
        1. Return ONLY valid JSON.
        2. Start with {{.
        
        JSON FORMAT: {{ "score": 0.85 }}
        """,
        input_variables=["query", "cv", "profile", "depth", "content", "metadata"]
    )
    chain = prompt | llm | JsonOutputParser()
    try:
        res = chain.invoke({
            "query": state["user_query"],
            "cv": json.dumps(state["context_data"]["cv"], ensure_ascii=False),
            "profile": str(state["profile"]),
            "depth": node.depth,
            "content": node.content,
            "metadata": str(node.metadata)
        })
        return float(res.get("score", 0.5))
    except:
        return 0.5

def prune_frontier(state: AgentState) -> AgentState:
    """
    Node 4: Selects the top K (Beam Width) nodes for the next iteration.
    """
    print(f"--- Node: Prune Frontier (Width {CONFIG.beam_width}) ---")
    frontier = state["frontier"]
    if not frontier:
        return state
        
    # Sort by PATH score desc
    sorted_frontier = sorted(frontier, key=lambda x: x.path_score, reverse=True)
    beam = sorted_frontier[:CONFIG.beam_width]
    
    return {**state, "frontier": beam}

def check_stop_condition(state: AgentState) -> str:
    """
    Conditional Logic: Continue or Stop?
    """
    frontier = state["frontier"]
    best_node = state["best_node"]
    
    print(f"--- Check Stop: Depth {frontier[0].depth if frontier else '?'}, Best Score {best_node.path_score if best_node else 0} ---")
    
    if not frontier:
        return "finalize" # Dead end, return best so far
        
    current_depth = frontier[0].depth
    
    # 1. Max Depth
    if current_depth >= CONFIG.max_depth:
        return "finalize"
        
    # 2. Score Threshold (Early Exit)
    # Only if we are at least depth 1 (have a strategy)
    if best_node and best_node.path_score >= CONFIG.score_threshold and current_depth == CONFIG.max_depth:
         return "finalize"
         
    return "expand"

def finalize_output(state: AgentState) -> AgentState:
    """
    Node 5: Reconstructs path and output.
    """
    print("--- Node: Finalize Output ---")
    best_node = state["best_node"]
    tree_memory = state["tree_memory"]
    
    path = []
    curr = best_node
    while curr:
        path.append(curr)
        if curr.parent_id:
            curr = tree_memory.get(curr.parent_id)
        else:
            curr = None
    path.reverse() # Root -> Leaf
    
    # Construct reasoning trace
    trace = [f"[{n.depth}] {n.content} (Score: {n.path_score:.2f})" for n in path]
    
    # Final response is the content of the leaf
    final_resp = best_node.content if best_node else "No suitable strategy found."
    strategy_label = path[1].content if len(path) > 1 else "Unknown"
    
    return {
        **state,
        "final_response": final_resp,
        "reasoning_trace": trace,
        "selected_strategy_label": strategy_label # Ad-hoc addition for verification
    }

# --- Graph ---

def create_tot_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("expand_frontier", expand_frontier)
    workflow.add_node("evaluate_frontier", evaluate_frontier)
    workflow.add_node("prune_frontier", prune_frontier)
    workflow.add_node("finalize_output", finalize_output)
    
    workflow.set_entry_point("retrieve_context")
    
    workflow.add_edge("retrieve_context", "expand_frontier")
    workflow.add_edge("expand_frontier", "evaluate_frontier")
    workflow.add_edge("evaluate_frontier", "prune_frontier")
    
    workflow.add_conditional_edges(
        "prune_frontier",
        check_stop_condition,
        {
            "expand": "expand_frontier",
            "finalize": "finalize_output"
        }
    )
    
    workflow.add_edge("finalize_output", END)
    
    return workflow.compile()
