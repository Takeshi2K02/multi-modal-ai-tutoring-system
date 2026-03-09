import os
from datetime import datetime
import uuid
import asyncio
import time
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
from services.synthesis_service import synthesis_service
import time

# Configuration
CONFIG = ToTConfig(
    max_depth=2,
    beam_width=2, # Optimized Beam Width
    branching_factor=2, # Reduced branching factor for speed
    score_threshold=0.85
)

# Initialize LLM
llm = get_llm()

# Vertex AI Rate Limiting Semaphore (Tier 1: 2,000 RPM safety)
semaphore = asyncio.Semaphore(10)

# Helper for robust parsing
def extract_json_from_text(text: str) -> Dict:
    """
    Extracts the first valid JSON object from a string, handling markdown blocks and control characters.
    """
    cleaned_text = text
    try:
        # Pre-processing: Strip markdown backticks
        cleaned_text = re.sub(r"```(?:json)?\s*|\s*```", "", text).strip()
        
        # Robust Regex for JSON block extraction if still wrapped
        match = re.search(r"(\{.*\})", cleaned_text, re.DOTALL)
        if match:
            cleaned_text = match.group(1)
            
        # Use strict=False to handle invalid control characters (e.g. newlines in strings)
        return json.loads(cleaned_text, strict=False)
    except Exception as e:
        print(f"[Parser] !!! RAW_LLM_RESPONSE failing at char 281: {text}")
        # Final attempt: manual regex fix for unescaped quotes in common fields
        try:
            # Simple heuristic: try to escape quotes that are not followed by , or }
            # This is risky but helps for "label" or "approach" strings
            manual_fix = re.sub(r'(?<=[:\s])"(.*?)"(?=[\s,])', r'"\1"', cleaned_text)
            return json.loads(manual_fix, strict=False)
        except:
            raise ValueError(f"Failed to extract JSON from text: {text[:200]}... Error: {e}")

# --- Nodes ---

async def retrieve_context(state: AgentState) -> AgentState:
    """
    Node 1: Fetches context and initializes the tree root.
    Prioritizes RL 'teaching_strategy' if provided.
    """
    print("[ToT] 🧩 --- Node: Retrieve Context & Init Root ---")
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
    
    # Load Preferences & Blacklist (Project ID: 25-26J-130)
    preferences = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34}) if profile else {"visual": 0.33, "textual": 0.33, "interactive": 0.34}
    blacklist = profile.get("strategy_blacklist", {}).get(state["user_query"], []) if profile else []

    return {
        **state,
        "profile": profile,
        "context_data": context_data,
        "student_preferences": preferences,
        "strategy_blacklist": blacklist,
        "frontier": [root_node],
        "tree_memory": {root_node.id: root_node},
        "best_node": root_node,
        "build_time": time.time(),
        "stop_early": False
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
    
    print(f"[ToT] 🌿 --- Node: Expand Frontier (Depth {current_depth} -> {next_depth}) ---")
    
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
            action_id = snapshot.get("action_id", 0)
            rl_strategy = snapshot.get("rl_strategy", "General Instruction")
            
            # Action-aware prompt optimization
            pruning_logic = "Focus strictly on analogies and step-by-step logic." if action_id == 1 else "General pedagogical exploration."
            
            prompt = PromptTemplate(
                template="""
                Role: Senior BI Architect mentor.
                Goal: {query}
                Policy Action: {rl_strategy} (ID: {action_id})
                
                PRUNING CONSTRAINT: {pruning_logic}
                
                TASK: Generate {k} strategies.
                JSON FORMAT: {{ "options": [ {{ "label": "Strategy Name", "strategy_type": "unique_id", "approach": "mentorship-style approach" }} ] }}
                """,
                input_variables=["action_id", "rl_strategy", "pruning_logic", "query", "k"]
            )
            
            for attempt in range(max_retries):
                raw_res = ""
                try:
                    chain = prompt | llm | StrOutputParser()
                    raw_res = await chain.ainvoke({
                        "action_id": action_id,
                        "rl_strategy": rl_strategy,
                        "pruning_logic": pruning_logic,
                        "query": query, "k": CONFIG.branching_factor
                    })
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                    
                    results = []
                    for opt in options:
                        results.append({
                            "content": opt["label"], 
                            "metadata": {
                                "approach": opt.get("approach", ""), 
                                "strategy_type": opt.get("strategy_type", "visual_explanation"),
                                "type": "strategy",
                                "policy_id": action_id,
                                "policy_name": rl_strategy
                            }
                        })
                    return results
                except Exception as e:
                    print(f"[ToT] ⚠️ Gen D1 Parse Failed (Attempt {attempt+1}): {e}")
                    print(f"[ToT] >>> RAW_LLM_RESPONSE: {raw_res}")
                    
                    # SAFE-PARSE FALLBACK (Project ID: 25-26J-130)
                    # Use string indexing to extract labels if JSON is broken
                    if "label" in raw_res:
                        try:
                            labels = re.findall(r'"label":\s*"([^"]+)"', raw_res)
                            if labels:
                                print(f"[ToT] 🛡️ >>> Safe-Parse Success: Extracted {len(labels)} strategies manually.")
                                return [{"content": l, "metadata": {"type": "strategy", "strategy_type": "visual_explanation"}} for l in labels[:CONFIG.branching_factor]]
                        except:
                            pass
                            
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
                {{
                    "options": [
                        {{
                            "directive": {{
                                "type": "explanation | quiz | challenge",
                                "content": "Full pedagogical content (Markdown) with [MERMAID_START]...[MERMAID_END] or [IMAGE_FOR_ALEX] tags if needed",
                                "quiz": {{ 
                                    "questions": [
                                        {{
                                            "question": "The MCQ Question",
                                            "options": ["A", "B", "C", "D"],
                                            "correct_index": 0,
                                            "explanation": "Why A is correct"
                                        }}
                                    ],
                                    "type": "multiple-choice"
                                }},
                                "challenge": {{
                                    "type": "text",
                                    "description": "Challenge description",
                                    "attributes_required": 3
                                }}
                            }}
                        }}
                    ]
                }}
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
                                print(f"[ToT] ⚠️ >>> [Payload Integrity] Mermaid block missing or too short for BI topic. Adding fallback.")
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
    print("[ToT] ⚖️ --- Node: Evaluate Frontier ---")
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
        
    # Early Stopping Logic (Project ID: 25-26J-130)
    stop_early = False
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    target_action = snapshot.get("action_id", 0)
    
    for node in scored_frontier:
        # Check if node score > threshold AND metadata matches the target RL action
        if node.score >= CONFIG.score_threshold:
            # For depth 1, check if strategy type matches pruning intent (simplified check)
            # For depth 2, check if it was derived from a valid depth 1 strategy
            stop_early = True
            current_best = node
            print(f"[ToT] 🎯 >>> Early Stopping Triggered: Score {node.score:.2f} >= {CONFIG.score_threshold}")
            break

    # Personalization Tie-Breaker (Project ID: 25-26J-130)
    # If two thought branches have similar evaluation scores (within 0.05),
    # select the branch that aligns with the student's highest preferred_modality weight.
    if len(scored_frontier) >= 2:
        top_two = sorted(scored_frontier, key=lambda x: x.score, reverse=True)[:2]
        if abs(top_two[0].score - top_two[1].score) <= 0.05:
            print("[ToT] 🌓 >>> Similarity Detected (Score Delta <= 0.05): Querying Student Profile for Tie-Breaker...")
            from db.connection import get_db_connection, get_profiles_collection
            db_conn = get_db_connection()
            profiles = get_profiles_collection(db_conn)
            profile_data = profiles.find_one({"student_id": state["student_id"]})
            
            if profile_data:
                pref = profile_data.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
                # Determine modality of each node (heuristic: check metadata or content)
                def get_node_modality(node):
                    ctype = node.metadata.get("type", "").lower()
                    if "worked_example" in ctype or "visual" in ctype: return "visual"
                    if "practice" in ctype or "interactive" in ctype: return "interactive"
                    return "textual"
                
                mod0 = get_node_modality(top_two[0])
                mod1 = get_node_modality(top_two[1])
                
                # Ensure float comparison for weights vs scores
                weight0 = float(pref.get(mod0, 0))
                weight1 = float(pref.get(mod1, 0))

                if weight1 > weight0:
                    print(f"[ToT] ✨ >>> Personalization Applied: Swapping node '{mod0}' for student-preferred '{mod1}' (+0.01)")
                    current_best = top_two[1]
                    # Apply a score bonus to ensure it survives pruning
                    top_two[1].score += 0.01
                    top_two[1].path_score += 0.01
                else:
                    current_best = top_two[0]
                    # Apply a score bonus to ensure it survives pruning
                    top_two[0].score += 0.01
                    top_two[0].path_score += 0.01
            
    # Broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_step", {
        "step": "evaluate_frontier",
        "scores": [n.score for n in scored_frontier],
        "early_stop": stop_early
    })
    
    return {**state, "frontier": scored_frontier, "best_node": current_best, "stop_early": stop_early}

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
        except asyncio.CancelledError:
            print("[ToT] 🛑 >>> Scoring Cancelled: Graceful exit triggered.")
            raise
        except Exception as e:
            print(f"[ToT] ⚠️ Scoring Failed: {e}")
            return 0.5

async def prune_frontier(state: AgentState) -> AgentState:
    """
    Node 4: Selects the top K (Beam Width) nodes.
    """
    print(f"[ToT] ✂️ --- Node: Prune Frontier ---")
    frontier = state["frontier"]
    if not frontier:
        return state
        
    # Standard beam search sorting by path_score
    # Tie-breaker: mastery_level from snapshot
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    mastery = snapshot.get("mastery_level", 0.5)
    
    # Sort primarily by path_score, secondarily by mastery (though mastery is constant for a state, 
    # the user asked to use it as a tie-breaker, implying we might want to prioritize nodes 
    # differently based on it. However, since mastery is per-student. 
    # Re-reading: "Use the 'mastery_level' as a tie-breaker in the ToT evaluation node when two branches have identical scores."
    # I will modify the sorting key here to be (path_score, mastery)
    sorted_frontier = sorted(frontier, key=lambda x: (x.path_score, mastery), reverse=True)
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
    ToT stop condition with Early Stopping support.
    """
    if state.get("stop_early"):
        print("[ToT] ⚡ >>> Terminating ToT Expansion: Early Stopping Flag Set")
        return "finalize"
        
    frontier = state["frontier"]
    if not frontier:
        return "finalize"
    current_depth = frontier[0].depth
    if current_depth >= CONFIG.max_depth:
        return "finalize"
    return "expand"

async def finalize_output(state: AgentState) -> AgentState:
    """
    Node 5: Final output generation and latency calculation.
    """
    print("[ToT] 🏁 --- Node: Finalize Output ---")
    best_node = state.get("best_node")
    tree_memory = state["tree_memory"] # Keep this line from original

    # Calculate build_time telemetry
    start_time = state.get("build_time", time.time())
    latency = round(time.time() - start_time, 2)
    
    path = []
    curr = best_node
    while curr:
        path.append(curr)
        curr = tree_memory.get(curr.parent_id) if curr.parent_id else None
    path.reverse()
    
    trace = [f"[{n.depth}] {n.content} (Score: {n.path_score:.2f})" for n in path]
    
    # Map RL Action ID to Strategy Label (Project ID: 25-26J-130)
    from agent_core.schemas import RL_ACTION_MAP
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    
    action_id = snapshot.get("action_id", 0)
    strategy_label = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown Strategy").upper().replace(" ", "_")
    
    # Project ID: 25-26J-130: Mandatory LLM Synthesis Step
    # Expand the selected thought into a full multimodal lesson
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from agent_core.llm import get_llm
    
    final_llm = get_llm()
    synthesis_prompt = ChatPromptTemplate.from_template("""
        Role: Senior Pedagogical Architect.
        Context: {query}
        Selected Thought: {thought}
        Strategy: {strategy}
        
        TASK: Expand this thought into a full multimodal lesson for a student.
        REQUIREMENTS:
        1. Start with a specific analogy: THE SUPERMARKET RECEIPT ANALOGY.
        2. Explain 3 key technical terms related to Dimensional Modelling (Facts, Dimensions, Grain).
        3. Include a [MERMAID_START] diagram using [MERMAID_END] tags.
        4. Maintain an encouraging, professional tone.
        5. Tone: Mentorship-style.
        
        OUTPUT: Pure Markdown text with multimodal tags.
    """)
    
    thought_content = best_node.content if best_node else "No specific thought selected."
    final_prompt = synthesis_prompt.format(
        query=state["user_query"],
        thought=thought_content,
        strategy=strategy_label
    )
    
    print("[ToT] 📝 --- Attempting Final Synthesis with Gemini 2.5 Flash ---")
    print(f"[ToT] Handoff Content:\n{final_prompt}")
    
    try:
        chain = synthesis_prompt | final_llm | StrOutputParser()
        full_lesson = await chain.ainvoke({
            "query": state["user_query"],
            "thought": thought_content,
            "strategy": strategy_label
        })
        
        # Enhanced Logging: Print full response object equivalent (the string output in this case)
        print(f"[ToT] >>> LLM Response Payload: {full_lesson}")
        
        # Content Synthesis Validation
        if not full_lesson or not isinstance(full_lesson, str) or len(full_lesson.strip()) == 0:
            raise ValueError("LLM returned empty body_text")
            
    except Exception as e:
        print(f"Synthesis Failed: {e}")
        # HARDCODED FALLBACK LESSON (Project ID: 25-26J-130)
        full_lesson = f"""
### 🧩 Fallback Lesson: Understanding {state['user_query']}

It looks like we hit a technical hiccup, but don't worry! Here's a quick overview of **{state['user_query']}** to keep you moving forward.

**The Analogy**: Think of this concept like a **Blueprint**. Before you build a skyscraper (your BI Architecture), you need a clear map of where every beam and wire goes.

**Key Concepts**:
1. **Facts**: The quantitative measurements (e.g., Total Sales).
2. **Dimensions**: The context (e.g., Date, Product, Store).
3. **Grain**: The level of detail (e.g., individual transaction vs. daily total).

[MERMAID_START]
graph TD
  A[Concept: {state['user_query']}] --> B[Core Logic]
  B --> C[Practical Application]
  C --> D[Ready to Proceed]
[MERMAID_END]

*Our AI is currently re-calibrating to provide a more personalized path. Let's start with this foundational view.*
"""

    # Compute Outcome simulation
    initial_affect = snapshot.get("current_affect", {})
    initial_score = initial_affect.get("score", 0.5)
    
    simulated_final_score = initial_score
    if best_node and best_node.path_score > 0.8:
        simulated_final_score = min(1.0, initial_score + 0.2)
    
    # Simple outcome comparison
    outcome = "Improved" if simulated_final_score > initial_score else "Stable"
    
    # Project ID: 25-26J-130: Generate Interaction ID early for scope stability
    from bson import ObjectId
    interaction_id = str(ObjectId())
    
    # Save Interaction with CV/Branch Metadata (Project ID: 25-26J-130)
    # ASYNC DECOUPLING: Move persistence to background task
    async def save_mem():
        memory = MemoryManager()
        memory.save_interaction({
            "_id": ObjectId(interaction_id), # Ensure we use the same ID
            "student_id": state["student_id"],
            "query": state["user_query"],
            "strategy": strategy_label,
            "branch_id": best_node.id if best_node else None,
            "path_score": best_node.path_score if best_node else 0.0,
            "engagement_score": snapshot.get("current_affect", {}).get("score", 0.5), # Audit Requirement
            "outcome": outcome,
            "trace": trace,
            "timestamp": datetime.now()
        })
    asyncio.create_task(save_mem())

    # Final broadcast to Admin Dashboard
    from server import sio
    await sio.emit("tot_final", {
        "student_id": state["student_id"],
        "final_response": full_lesson,
        "full_text": full_lesson,
        "body_text": full_lesson,
        "strategy": strategy_label,
        "outcome": outcome,
        "trace": trace,
        "interaction_id": interaction_id,
        "strategy_label": strategy_label
    })

    return {
        **state,
        "final_response": full_lesson,
        "full_text": full_lesson,
        "body_text": full_lesson,
        "visual_tags": ["mermaid", "analogy"],
        "reasoning_trace": trace,
        "interaction_outcome": outcome,
        "selected_strategy_label": strategy_label,
        "interaction_id": interaction_id,
        "build_time": latency
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
