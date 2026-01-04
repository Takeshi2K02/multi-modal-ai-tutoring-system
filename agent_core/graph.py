import os
import uuid
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import json
import re

from memory.student_memory import MemoryManager
from mocks.data_generators import get_mock_cv_inputs, get_mock_rl_strategy
from agent_core.schemas import AgentState, ThoughtNode, ToTConfig
from agent_core.llm import get_llm
from agent_core.strategy_taxonomy import StrategyType
from agent_core.optimization import compute_outcome

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

# Helper for robust parsing
def extract_json_from_text(text: str) -> Dict:
    """
    Extracts the first valid JSON object from a string, handling markdown blocks
    and conversational preambles/postscripts common in local LLMs.
    """
    try:
        # First, try to find a JSON block between backticks
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
        # If no code block, try to find the first { and the last }
        # This catches "Here is the JSON: { ... } Hope that helps!"
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
            
        # Final fallback: try raw
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"Failed to extract JSON from text: {text[:100]}... Error: {e}")

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
    
    # ENRICHMENT: Map action_id to human-readable name for UI transparency
    from agent_core.schemas import RL_ACTION_MAP
    action_id = rl_strategy.get("action_id", 2)
    current_policy = RL_ACTION_MAP.get(action_id, {"name": "Unknown Policy"})
    rl_strategy["policy_name"] = current_policy["name"]
    
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

    max_retries = 3
    base_delay = 5

    if target_depth == 1:
        # Generate Strategies
        # ENFORCE RL POLICY: Get action_id and look up allowed strategies
        rl_data = context.get("rl_hint", {})
        # Handle both dict and string representation if necessary (mocks return dict)
        action_id = rl_data.get("action_id", 2) # Default to Hint (2) if missing
        
        from agent_core.schemas import RL_ACTION_MAP
        policy = RL_ACTION_MAP.get(action_id, RL_ACTION_MAP[2])
        allowed_strategies = ", ".join(policy["allowed"])
        policy_name = policy["name"]

        valid_strategies = [st.value for st in StrategyType]
        
        prompt = PromptTemplate(
            template="""
            Role: You are a strict JSON data generator.
            
            Student: {profile}
            
            REAL-TIME SIGNALS:
            CV Data: {cv}
            
            RL POLICY INSTRUCTION (MANDATORY):
            - Policy Action: "{policy_name}" (ID: {action_id})
            - ALLOWED STRATEGIES: [{allowed_strategies}]
            
            Goal: {query}
            
            TASK: Generate {k} distinct execution strategies that strictly align with the ALLOWED STRATEGIES list.
            
            CRITICAL: You MUST use one of these fixed 'strategy_type' IDs:
            {valid_strategies}
            
            OUTPUT RULES:
            1. Return ONLY valid JSON.
            2. The "label" MUST be one of the Allowed Strategies (or a very close variation).
            3. "strategy_type" MUST be one of the valid IDs.
            4. "approach" should explain how you will apply it.
            
            JSON FORMAT:
            {{ "options": [ {{ "label": "Strategy Name", "strategy_type": "unique_id", "approach": "Description" }}, ... ] }}
            """,
            input_variables=["profile", "cv", "policy_name", "action_id", "allowed_strategies", "query", "k", "valid_strategies"]
        )
        
        for attempt in range(max_retries):
            try:
                # Use StrOutputParser + Custom Extraction for robustness against "Chatty" LLMs
                chain = prompt | llm | StrOutputParser()
                raw_res = chain.invoke({
                    "profile": str(profile), 
                    "cv": json.dumps(context["cv"], ensure_ascii=False), 
                    "policy_name": policy_name,
                    "action_id": action_id,
                    "allowed_strategies": allowed_strategies,
                    "query": query, "k": CONFIG.branching_factor,
                    "valid_strategies": ", ".join(valid_strategies)
                })
                
                res = extract_json_from_text(raw_res)

                # ROBUST PARSING: Handle if LLM returns a List directly instead of {"options": [...]}
                options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                
                # Tag nodes with policy info for tracing
                results = []
                for opt in options:
                    results.append({
                        "content": opt["label"], 
                        "metadata": {
                            "approach": opt.get("approach", ""), 
                            "strategy_type": opt.get("strategy_type", "visual_explanation"),
                            "type": "strategy",
                            "policy_id": action_id,
                            "policy_name": policy_name
                        }
                    })
                return results

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
            
            TASK: Generate {k} variations of specific content directives.
            
            OUTPUT RULES:
            1. Return ONLY valid JSON.
            2. Start output immediately with {{.
            
            JSON FORMAT: 
            {{
                "options": [
                    {{
                        "directive": {{
                            "type": "explanation | quiz | summary",
                            "format": "text",
                            "parameters": {{ "tone": "encouraging", "complexity": "low" }},
                            "content": "The actual full text of the explanation..."
                        }},
                        "focus": "Main focus/theme of this variation"
                    }}
                ]
            }}
            """,
            input_variables=["profile", "cv", "strategy", "approach", "query", "k"]
        )
        for attempt in range(max_retries):
            try:
                chain = prompt | llm | StrOutputParser()
                parent_approach = parent_node.metadata.get("approach", "")
                raw_res = chain.invoke({
                    "profile": str(profile), 
                    "cv": json.dumps(context["cv"], ensure_ascii=False), 
                    "strategy": parent_node.content, "approach": parent_approach,
                    "query": query, "k": CONFIG.branching_factor
                })
                
                res = extract_json_from_text(raw_res)
                
                # ROBUST PARSING: Handle if LLM returns a List directly instead of {"options": [...]}
                options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                
                # Transform into ThoughtNodes
                # We store the "content" text in node.content (for UI visibility)
                # We store the full "directive" object in node.metadata (for Content Generator)
                children = []
                for opt in options:
                    directive = opt.get("directive", {})
                    # Fallback if LLM messes up structure but gives text
                    content_text = directive.get("content", opt.get("text", "No content provided"))
                    
                    children.append({
                        "content": content_text,
                        "metadata": {
                            "focus": opt.get("focus", ""),
                            "type": "response",
                            "directive": directive # The full structured output
                        }
                    })
                return children

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
    # Use LLM to score relevance
    # Create Prompt with Taxonomy
    valid_strategies = [st.value for st in StrategyType]
    
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
        3. NO markdown.
        
        JSON FORMAT: {{ "score": 0.85 }}
        """,
        input_variables=["query", "cv", "profile", "depth", "content", "metadata"]
    )
    chain = prompt | llm | StrOutputParser()
    
    try:
        raw_res = chain.invoke({
            "query": state["user_query"],
            "cv": json.dumps(state["context_data"]["cv"], ensure_ascii=False),
            "profile": str(state["profile"]),
            "depth": node.depth,
            "content": node.content,
            "metadata": str(node.metadata)
        })
        
        # Robust extraction
        res = extract_json_from_text(raw_res)
        
        score = res.get("score")
        if score is None:
            print(f"Scoring Warning: No 'score' key in {res}")
            return 0.5
        return float(score)
    except Exception as e:
        print(f"Scoring Failed for node {node.id[:8]}: {e}")
        return 0.5

def prune_frontier(state: AgentState) -> AgentState:
    """
    Node 4: Selects the top K (Beam Width) nodes for the next iteration.
    """
    print(f"--- Node: Prune Frontier (Width {CONFIG.beam_width}) ---")
    frontier = state["frontier"]
    if not frontier:
        return state
        
    # Tie-Breaking Logic
    # 1. Identify Tie: Check if top N candidates have similar scores
    # 2. Resolve: Use Student Learning Preferences (Confidence)
    
    sorted_frontier = sorted(frontier, key=lambda x: x.path_score, reverse=True)
    
    # Enrich frontier with Preference Confidence for sorting
    profile = state["profile"]
    preferences = profile.get("learning_preferences", {})
    
    def get_preference_score(node):
        # We only have strategy type at depth 1. At depth 2, we inherit from parent.
        st_type = node.metadata.get("strategy_type")
        if not st_type and node.parent_id:
             # Try to find parent
             from memory.student_memory import MemoryManager # Lazy import to avoid cycle if any
             # Actually we use tree_memory in state
             tree_mem = state["tree_memory"]
             parent = tree_mem.get(node.parent_id)
             if parent:
                 st_type = parent.metadata.get("strategy_type")
        
        if st_type and st_type in preferences:
            return preferences[st_type]["confidence"]
        return 0.5 # Default neutral

    # Check for meaningful ties in the top candidates
    # We define a "tie" as scores within 0.05
    tie_trace = None
    
    if len(sorted_frontier) >= 2:
        top_1 = sorted_frontier[0]
        top_2 = sorted_frontier[1]
        
        if abs(top_1.path_score - top_2.path_score) < 0.05:
            # Tie detected!
            score_diff = abs(top_1.path_score - top_2.path_score)
            p1 = get_preference_score(top_1)
            p2 = get_preference_score(top_2)
            
            tie_trace = {
                "triggered": True,
                "candidates": [
                    {"content": top_1.content, "score": top_1.path_score, "pref_conf": p1},
                    {"content": top_2.content, "score": top_2.path_score, "pref_conf": p2}
                ],
                "resolution": "Student Preference Model"
            }
            
            # Re-sort using Tuple: (Path Score rounded, Preference Score, Original Score)
            # This prioritizes Preference when Path Score is roughly equal
            sorted_frontier = sorted(frontier, key=lambda x: (
                round(x.path_score * 10), # Group into 0.1 buckets roughly
                get_preference_score(x),
                x.path_score
            ), reverse=True)
            
            print(f"--- TIE BREAKING TRIGGERED: {top_1.content} vs {top_2.content} ---")

    beam = sorted_frontier[:CONFIG.beam_width]
    
    new_state = {**state, "frontier": beam}
    if tie_trace:
        new_state["tie_break_trace"] = tie_trace
        
    return new_state

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
    
    # Extract Policy Info from Strategy Node (Depth 1)
    policy_id = "N/A"
    policy_name = "N/A"
    strategy_type = "visual_explanation" # Default
    
    if len(path) > 1:
        strategy_node = path[1]
        policy_id = strategy_node.metadata.get("policy_id", "N/A")
        policy_name = strategy_node.metadata.get("policy_name", "N/A")
        strategy_type = strategy_node.metadata.get("strategy_type", "visual_explanation")

    # COMPUTE OUTCOME & UPDATE PROFILE
    # We need "previous" CV state. Since we don't have a real time loop in this script, 
    # we'll simulate it by comparing 'test_cv_state' (initial) vs a 'final' state.
    # In a real system, we'd persist the session.
    # For now, we will Mock a "Post-Interaction" CV state to demonstrate the logic.
    
    initial_cv = state["context_data"]["cv"]
    # Mock result: If strategy matched preference, improve engagement? 
    # Or just random for now + logic?
    # Let's derive it from the Node Score effectively. High Node Score -> likely good outcome.
    
    simulated_final_cv = initial_cv.copy()
    if best_node and best_node.path_score > 0.8:
        simulated_final_cv["engagement_score"] += 0.2
        simulated_final_cv["engagement_state"] = "highly_engaged"
    else:
        simulated_final_cv["engagement_score"] -= 0.1
        
    outcome = compute_outcome(initial_cv, simulated_final_cv)
    
    # Update DB
    memory = MemoryManager()
    memory.update_learning_preference(
        state["student_id"], 
        strategy_type, 
        outcome["success"]
    )
    
    # Log Interaction
    interaction_log = {
        "student_id": state["student_id"],
        "query": state["user_query"],
        "strategy_label": strategy_label,
        "strategy_type": strategy_type,
        "outcome": outcome,
        "path_score": best_node.path_score if best_node else 0,
        "tie_break": state.get("tie_break_trace")
    }
    memory.save_interaction(interaction_log)

    return {
        **state,
        "final_response": final_resp,
        "reasoning_trace": trace,
        "selected_strategy_label": strategy_label,
        "policy_action_id": policy_id,
        "policy_action_name": policy_name,
        "interaction_outcome": outcome
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
