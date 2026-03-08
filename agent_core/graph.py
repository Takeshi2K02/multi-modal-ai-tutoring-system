import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
import json
import re

from memory.student_memory import MemoryManager
from mocks.data_generators import get_mock_cv_inputs, get_mock_rl_strategy
from agent_core.schemas import AgentState, ThoughtNode, ToTConfig, StudentStateSnapshot
from agent_core.llm import get_llm
from agent_core.strategy_taxonomy import StrategyType
from agent_core.optimization import compute_outcome
from agent_core.snapshot import get_student_snapshot
from services.vector_factory import get_vector_db

# Configuration
CONFIG = ToTConfig(
    max_depth=2,
    beam_width=2,
    branching_factor=3,
    score_threshold=0.85
)

# Initialize LLM
llm = get_llm()

# Vertex AI Rate Limiting Semaphore (Tier 1: 2,000 RPM safety)
semaphore = asyncio.Semaphore(10)

# Helper for robust parsing
def extract_json_from_text(text: str) -> Dict:
    """
    Extracts the first valid JSON object from a string, handling markdown blocks.
    """
    try:
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"Failed to extract JSON from text: {text[:100]}... Error: {e}")

# --- Nodes ---

async def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches context and initializes the tree root.
    Prioritizes RL 'teaching_strategy' if provided.
    """
    print("--- Node: Retrieve Context & Init Root ---")
    memory = MemoryManager()
    student_id = state["student_id"]
    
    profile = memory.get_student_profile(student_id)
    
    # --- TIME-SERIES SNAPSHOT INTEGRATION ---
    # Non-blocking lookup of latest CV/RL/Performance state
    snapshot = get_student_snapshot(student_id)
    
    # --- RAG INTEGRATION ---
    vectordb = get_vector_db()
    rag_results = vectordb.search(state["user_query"], top_k=5)
    rag_context = "\n---\n".join([r["text"] for r in rag_results])
    
    context_data = {
        "snapshot": snapshot.dict(),
        "history": memory.get_recent_history(student_id),
        "rag_evidence": rag_context
    }

    # Initialize Root Node
    root_node = ThoughtNode(
        depth=0,
        content=f"Root: Goal='{state['user_query']}'",
        score=1.0,
        path_score=1.0,
        metadata={"type": "root"}
    )
    
    # Broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_step", {
        "step": "retrieve_context",
        "snapshot": snapshot.dict(),
        "student_id": student_id,
        "query": state["user_query"]
    })
    
    return {
        **state,
        "profile": profile,
        "context_data": context_data,
        "frontier": [root_node],
        "tree_memory": {root_node.id: root_node},
        "best_node": root_node
    }

async def expand_frontier(state: AgentState) -> AgentState:
    """
    Node 2: Expands the current frontier by generating thoughts.
    Uses async gathering for efficiency.
    """
    frontier = state["frontier"]
    if not frontier:
        return state

    current_depth = frontier[0].depth
    next_depth = current_depth + 1
    
    print(f"--- Node: Expand Frontier (Depth {current_depth} -> {next_depth}) ---")
    
    tree_memory = state["tree_memory"].copy()
    
    # Generate children for all nodes in frontier concurrently
    tasks = [_generate_children_content(state, node, next_depth) for node in frontier]
    all_children_contents = await asyncio.gather(*tasks)
    
    new_frontier = []
    for node, children_contents in zip(frontier, all_children_contents):
        for content in children_contents:
            child = ThoughtNode(
                parent_id=node.id,
                depth=next_depth,
                content=content["content"],
                metadata=content.get("metadata", {})
            )
            new_frontier.append(child)
            tree_memory[child.id] = child
            
    # Broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_step", {
        "step": "expand_frontier",
        "depth": next_depth,
        "new_nodes_count": len(new_frontier)
    })
            
    return {**state, "frontier": new_frontier, "tree_memory": tree_memory}

async def _generate_children_content(state: AgentState, parent_node: ThoughtNode, target_depth: int) -> List[Dict]:
    """
    Helper to generate content using LLM with Rate Limiting Semaphore.
    """
    profile = state["profile"]
    context = state["context_data"]
    query = state["user_query"]
    
    max_retries = 3
    base_delay = 2

    async with semaphore:
        if target_depth == 1:
            snapshot = context.get("snapshot", {})
            valid_strategies = [st.value for st in StrategyType]
            policy_name = snapshot.get("rl_strategy", "General Instruction")
            
            prompt = PromptTemplate(
                template="""
                Role: You are a Senior BI Architect mentoring a 'BI Engineering Intern' at Mack Air/John Keells.
                
                Student Profile: {profile}
                Student State (Snapshot): {snapshot}
                Goal: {query}
                
                GROUNDED EVIDENCE (RAG):
                {rag_evidence}
                
                TASK: Generate {k} strategies that match the RL Policy: {policy_name}.
                STRICT REQUIREMENT: Prioritize GROUNDED EVIDENCE over generic knowledge. 
                If discussing Data Types, explain them via SQL Schemas, Facts/Dimensions, and Data Warehousing concepts.
                
                JSON FORMAT:
                {{ "options": [ {{ "label": "Strategy Name", "strategy_type": "unique_id", "approach": "mentorship-style approach" }}, ... ] }}
                """,
                input_variables=["profile", "snapshot", "policy_name", "rag_evidence", "query", "k", "valid_strategies"]
            )
            
            for attempt in range(max_retries):
                try:
                    chain = prompt | llm | StrOutputParser()
                    raw_res = await chain.ainvoke({
                        "profile": str(profile), 
                        "snapshot": json.dumps(snapshot),
                        "policy_name": snapshot.get("rl_strategy", "General Instruction"),
                        "rag_evidence": context.get("rag_evidence", ""),
                        "query": query, "k": CONFIG.branching_factor,
                        "valid_strategies": ", ".join(valid_strategies)
                    })
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                    action_id = snapshot.get("action_id", 2)
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
                    print(f"Gen D1 Failed: {e}")
                    await asyncio.sleep(base_delay * (attempt + 1))
            return []

        elif target_depth == 2:
            snapshot = context.get("snapshot", {})

            prompt = PromptTemplate(
                template="""
                Role: You are a Senior BI Architect presenting a lecture to a 'BI Engineering Intern' at Mack Air/John Keells.
                
                Context (Grounded Evidence):
                {rag_evidence}
                
                Goal: {query}
                Strategy: {strategy} ({approach})
                
                TASK: Provide {k} variations.
                STRICT REQUIREMENT: 
                1. Anchored primarily in Grounded Evidence.
                2. Use BI terminology (Facts, Dimensions, Star Schemas, Warehousing).
                3. TRIGGER MULTIMODAL RENDERING: If technical structure is complex, include a Mermaid.js diagram using tags:
                   [MERMAID_START]
                   graph TD
                   ...
                   [MERMAID_END]
                
                STRICT JSON OUTPUT FORMAT (MANDATORY):
                {
                    "options": [
                        {
                            "directive": {
                                "type": "explanation | quiz | challenge",
                                "content": "Full pedagogical content (Markdown) with [MERMAID_START]...[MERMAID_END] or [IMAGE_FOR_ALEX] tags if needed",
                                "quiz": { 
                                    "questions": [
                                        {
                                            "question": "The MCQ Question",
                                            "options": ["A", "B", "C", "D"],
                                            "correct_index": 0,
                                            "explanation": "Why A is correct"
                                        }
                                    ],
                                    "type": "multiple-choice"
                                },
                                "challenge": {
                                    "type": "text",
                                    "description": "Challenge description",
                                    "attributes_required": 3
                                }
                            }
                        }
                    ]
                }
                """,
                input_variables=["rag_evidence", "strategy", "approach", "query", "k"]
            )
            for attempt in range(max_retries):
                try:
                    chain = prompt | llm | StrOutputParser()
                    raw_res = await chain.ainvoke({
                        "rag_evidence": context.get("rag_evidence", ""),
                        "strategy": parent_node.content, 
                        "approach": parent_node.metadata.get("approach", ""),
                        "query": query, "k": CONFIG.branching_factor
                    })
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                    
                    children = []
                    for opt in options:
                        directive = opt.get("directive", {})
                        # Robust extraction: directive.content -> opt.text -> opt.content -> opt (if string)
                        content_val = directive.get("content") or opt.get("text") or opt.get("content")
                        if not content_val and isinstance(opt, str):
                            content_val = opt
                        
                        if not content_val:
                            content_val = "No content"
                        
                        # PAYLOAD INTEGRITY CHECK for BI Architecture/ETL/Schema
                        bi_keywords = ['architecture', 'etl', 'schema', 'data warehouse', 'star schema', 'snowflake']
                        is_bi_technical = any(k in query.lower() for k in bi_keywords) or any(k in parent_node.content.lower() for k in bi_keywords)
                        
                        if is_bi_technical and target_depth == 2:
                            # Verify Mermaid tags are present and have content
                            mermaid_match = re.search(r"\[MERMAID_START\]([\s\S]+?)\[MERMAID_END\]", str(content_val))
                            if not mermaid_match or len(mermaid_match.group(1).strip()) < 10:
                                print(f">>> [Payload Integrity] Mermaid block missing or too short for BI topic. Adding fallback.")
                                # We can't easily re-run here without recursion, so we append a fallback structural block if missing
                                if "[MERMAID_START]" not in str(content_val):
                                    content_val = str(content_val) + "\n\n[MERMAID_START]\ngraph TD\n  A[Data Source] --> B[ETL Layer]\n  B --> C[Data Warehouse]\n  C --> D[Analytics]\n[MERMAID_END]"

                        # Ensure directive has the content for the UI
                        directive["content"] = str(content_val)
                            
                        children.append({
                            "content": str(content_val),
                            "metadata": {
                                "focus": opt.get("focus", ""),
                                "type": "response",
                                "directive": directive
                            }
                        })
                    return children
                except Exception as e:
                    print(f"Gen D2 Failed: {e}")
                    await asyncio.sleep(base_delay * (attempt + 1))
            return []

    return []

async def evaluate_frontier(state: AgentState) -> AgentState:
    """
    Node 3: Scores the new nodes in the frontier concurrently.
    """
    print("--- Node: Evaluate Frontier ---")
    frontier = state["frontier"]
    tree_memory = state["tree_memory"]
    
    if not frontier:
        return state

    tasks = [_score_node_content(state, node, tree_memory) for node in frontier]
    local_scores = await asyncio.gather(*tasks)
    
    scored_frontier = []
    current_best = state["best_node"]
    
    for node, local_score in zip(frontier, local_scores):
        parent = tree_memory.get(node.parent_id)
        parent_path_score = parent.path_score if parent else 1.0
        
        if node.depth == 1:
            path_score = local_score
        else:
            path_score = (parent_path_score + local_score) / 2
            
        node.score = local_score
        node.path_score = path_score
        scored_frontier.append(node)
        
    frontier_best = max(scored_frontier, key=lambda x: x.path_score) if scored_frontier else None
    if frontier_best:
        current_best = frontier_best

    # Broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_step", {
        "step": "evaluate_frontier",
        "scores": [n.score for n in scored_frontier]
    })
    
    return {**state, "frontier": scored_frontier, "best_node": current_best}

async def _score_node_content(state: AgentState, node: ThoughtNode, tree_memory: Dict[str, ThoughtNode]) -> float:
    """
    Scores the candidate path using Gemini.
    """
    snapshot = state["context_data"].get("snapshot", {})

    prompt = PromptTemplate(
        template="""
        Role: Pedagogical Scoring engine for Gemini 2.5 Flash.
        
        Goal: {query}
        Student State (Snapshot): {snapshot}
        Student Profile: {profile}
        
        Candidate Path: "{content}"
        Metadata: {metadata}
        
        SCORING (0.0 - 1.0):
        1. Empathy Score (Multiplier if deviation_alert is True).
        2. Alignment with RL Strategy: {rl_strategy}.
        3. Multi-modal Effectiveness for Trend: {trend}.
        
        JSON FORMAT: {{ "score": 0.xx }}
        """,
        input_variables=["query", "snapshot", "profile", "rl_strategy", "trend", "content", "metadata"]
    )
    
    async with semaphore:
        chain = prompt | llm | StrOutputParser()
        try:
            raw_res = await chain.ainvoke({
                "query": state["user_query"],
                "snapshot": json.dumps(snapshot),
                "profile": str(state["profile"]),
                "rl_strategy": snapshot.get("rl_strategy"),
                "trend": snapshot.get("engagement_trend"),
                "content": node.content,
                "metadata": str(node.metadata)
            })
            res = extract_json_from_text(raw_res)
            return float(res.get("score", 0.5))
        except Exception as e:
            print(f"Scoring Failed: {e}")
            return 0.5

async def prune_frontier(state: AgentState) -> AgentState:
    """
    Node 4: Selects the top K (Beam Width) nodes.
    """
    print(f"--- Node: Prune Frontier ---")
    frontier = state["frontier"]
    if not frontier:
        return state
        
    # Standard beam search sorting by path_score
    sorted_frontier = sorted(frontier, key=lambda x: x.path_score, reverse=True)
    beam = sorted_frontier[:CONFIG.beam_width]
    
    # Broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_step", {
        "step": "prune_frontier",
        "beam_size": len(beam)
    })
    
    return {**state, "frontier": beam}

def check_stop_condition(state: AgentState) -> str:
    """
    Standard ToT stop condition.
    """
    frontier = state["frontier"]
    if not frontier:
        return "finalize"
    current_depth = frontier[0].depth
    if current_depth >= CONFIG.max_depth:
        return "finalize"
    return "expand"

async def finalize_output(state: AgentState) -> AgentState:
    """
    Node 5: Finalizes response and updates student memory.
    """
    print("--- Node: Finalize Output ---")
    best_node = state["best_node"]
    tree_memory = state["tree_memory"]
    
    path = []
    curr = best_node
    while curr:
        path.append(curr)
        curr = tree_memory.get(curr.parent_id) if curr.parent_id else None
    path.reverse()
    
    trace = [f"[{n.depth}] {n.content} (Score: {n.path_score:.2f})" for n in path]
    final_resp = best_node.content if best_node else "No strategy found."
    strategy_label = path[1].content if len(path) > 1 else "Unknown"
    
    # Compute Outcome simulation
    snapshot = state["context_data"]["snapshot"]
    initial_affect = snapshot.get("current_affect", {})
    initial_score = initial_affect.get("score", 0.5)
    
    simulated_final_score = initial_score
    if best_node and best_node.path_score > 0.8:
        simulated_final_score = min(1.0, initial_score + 0.2)
    
    # Simple outcome comparison
    outcome = "Improved" if simulated_final_score > initial_score else "Stable"
    
    # Save Interaction
    memory = MemoryManager()
    memory.save_interaction({
        "student_id": state["student_id"],
        "query": state["user_query"],
        "strategy": strategy_label,
        "outcome": outcome,
        "trace": trace
    })

    # Final broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_final", {
        "student_id": state["student_id"],
        "final_response": final_resp,
        "outcome": outcome,
        "trace": trace
    })

    return {
        **state,
        "final_response": final_resp,
        "reasoning_trace": trace,
        "interaction_outcome": outcome
    }

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
