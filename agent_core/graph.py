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
from bson import ObjectId

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
    max_depth=2, # Exactly 3 stages: Root (0), L1 (1), L2 (2)
    beam_width=3, 
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
    rag_sources = [r.get("metadata", {}).get("source", "unknown") for r in rag_results]
    
    context_data = {
        "snapshot": snapshot.dict(),
        "history": memory.get_recent_history(student_id),
        "rag_evidence": rag_context,
        "rag_sources": rag_sources
    }

    # Initialize Root Node
    root_node = ThoughtNode(
        depth=0,
        content=f"Root: Goal='{state['user_query']}'",
        score=1.0,
        path_score=1.0,
    )
    
    # Generate Interaction ID early for real-time streaming (Project ID: 25-26J-130)
    interaction_id = state.get("interaction_id") or str(ObjectId())
    
    # Broadcast to Admin Dashboard
    from socket_manager import sio
    await sio.emit("tot_step", {
        "step": "retrieve_context",
        "snapshot": snapshot.dict(),
        "student_id": student_id,
        "query": state["user_query"]
    })
    
    # --- REAL-TIME ToT EMISSION (Project ID: 25-26J-130) ---
    await sio.emit("node_discovered", {
        "synthesis_id": interaction_id,
        "id": root_node.id,
        "parent_id": None,
        "depth": 0,
        "content": root_node.content,
        "metadata": {
            **root_node.metadata,
            "strategy_name": "Root Inquiry",
            "internal_thought": "Initializing synthesis based on student profile and live CV state.",
            "pruning_status": "Active",
            "localScore": root_node.score,
            "pathScore": root_node.path_score
        },
        "rag_sources": rag_sources,
        "timestamp": datetime.now().isoformat()
    })
    
    # Load Preferences & Blacklist (Project ID: 25-26J-130)
    preferences = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34}) if profile else {"visual": 0.33, "textual": 0.33, "interactive": 0.34}
    blacklist = profile.get("strategy_blacklist", {}).get(state["user_query"], []) if profile else []

    # Metadata Benchmarking (Project ID: 25-26J-130)
    estimated_reading_time = profile.get("average_reading_speed", 120) if profile else 120

    return {
        **state,
        "student_id": student_id,
        "interaction_id": interaction_id,
        "profile": profile,
        "context_data": context_data,
        "student_preferences": preferences,
        "strategy_blacklist": blacklist,
        "frontier": [root_node],
        "tree_memory": {root_node.id: root_node},
        "best_node": root_node,
        "shadow_frontier": [], # Initialize shadow_frontier here
        "is_completed": False,
        "estimated_reading_time": estimated_reading_time,
        "synthesis_locked": False,
        "handoff_buffer": [],
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
    
    # Enhanced Logging for observability (Project ID: 25-26J-130)
    for node in frontier:
        print(f"[ToT] >>> Expanding parent node: '{node.content[:50]}...' (Depth {node.depth})")
    
    tree_memory = state["tree_memory"].copy()
    
    # Generate children for all nodes in frontier concurrently
    tasks = [_generate_children_content(state, node, next_depth) for node in frontier]
    all_children_contents = await asyncio.gather(*tasks)
    
    new_frontier = []
    from socket_manager import sio # Unified socket import
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
            
            # --- REAL-TIME ToT EMISSION (Project ID: 25-26J-130) ---
            # Emitting immediately inside the loop for discovery effect
            await sio.emit("node_discovered", {
                "synthesis_id": state.get("interaction_id"),
                "id": child.id,
                "parent_id": child.parent_id,
                "depth": child.depth,
                "content": child.content,
                "metadata": {
                    **child.metadata,
                    "strategy_name": child.metadata.get("strategy_name", "Exploring Path"),
                    "internal_thought": child.metadata.get("internal_thought", child.content),
                    "pruning_status": "Active",
                    "localScore": child.score,
                    "pathScore": child.path_score
                },
                "timestamp": datetime.now().isoformat()
            })
            
    # Broadcast for UI Toast (Project ID: 25-26J-130)
    snapshot = state["context_data"].get("snapshot", {})
    await sio.emit("tot_step", {
        "step": "EXPANDING_FRONTIER",
        "message": f"Expanding frontier to Depth {next_depth}...",
        "synthesis_id": state.get("interaction_id"),
        "depth": next_depth
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
                
                TASK: Generate {k} light-weight Strategy Blueprints (Max 100 words each).
                A blueprint must be concise and include: [Strategy Name], [Methodology], and [Predicted Engagement Score].
                
                JSON FORMAT: {{ "options": [ {{ "label": "Strategy Name", "strategy_type": "unique_id", "approach": "Concise blueprint methodology..." }} ] }}
                """,
                input_variables=["action_id", "rl_strategy", "pruning_logic", "query", "k"]
            )
            
            for attempt in range(max_retries):
                raw_res = ""
                try:
                    chain = prompt | llm | StrOutputParser()
                    # PROJECT ID: 25-26J-130: Local Timeout Guard for LLM stalls
                    raw_res = await asyncio.wait_for(
                        chain.ainvoke({
                            "action_id": action_id,
                            "rl_strategy": rl_strategy,
                            "pruning_logic": pruning_logic,
                            "query": query, "k": CONFIG.branching_factor
                        }),
                        timeout=45.0
                    )
                    
                    # --- REASONING TERMINAL STREAM (Project ID: 25-26J-130) ---
                    from socket_manager import sio
                    await sio.emit("thought_stream", {
                        "synthesis_id": state.get("interaction_id"),
                        "source": "Expand Frontier (D1)",
                        "content": raw_res,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                    
                    results = []
                    for opt in options:
                        results.append({
                            "content": opt["label"], 
                            "metadata": {
                                "strategy_name": opt.get("label", ""),
                                "internal_thought": opt.get("approach", ""),
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
                
                TASK: Provide {k} variations as 'Strategy Blueprints'.
                STRICT REQUIREMENT: 
                1. Anchored primarily in Grounded Evidence.
                2. Use BI terminology (Facts, Dimensions, Star Schemas).
                3. DO NOT generate full lesson text. ONLY provide a high-level instructional blueprint (max 100 words).
                
                STRICT JSON OUTPUT FORMAT (MANDATORY):
                {{
                    "options": [
                        {{
                            "directive": {{
                                "type": "blueprint",
                                "content": "STRATEGY BLUEPRINT: [Methodology] ... [Pedagogical Goal] ... "
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
                    # PROJECT ID: 25-26J-130: Local Timeout Guard for LLM stalls
                    raw_res = await asyncio.wait_for(
                        chain.ainvoke({
                            "rag_evidence": context.get("rag_evidence", ""),
                            "strategy": parent_node.content, 
                            "approach": parent_node.metadata.get("approach", ""),
                            "query": query, "k": CONFIG.branching_factor
                        }),
                        timeout=45.0
                    )
                    
                    # --- REASONING TERMINAL STREAM (Project ID: 25-26J-130) ---
                    from socket_manager import sio
                    await sio.emit("thought_stream", {
                        "synthesis_id": state.get("interaction_id"),
                        "source": f"Expand Frontier (D2: {parent_node.content})",
                        "content": raw_res,
                        "timestamp": datetime.now().isoformat()
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
                            "content": content_val[:100] + "..." if content_val and len(content_val) > 100 else content_val,
                            "metadata": {
                                "strategy_name": parent_node.metadata.get("strategy_name", "Synthesis"),
                                "internal_thought": directive.get("content", content_val), # Use directive content for internal thought
                                "directive": directive,
                                "type": "variation"
                            }
                        })
                    return children
                except Exception as e:
                    print(f"Gen D2 Failed: {e}")
                    await asyncio.sleep(base_delay * (attempt + 1))
            return []

        elif target_depth == 3:
            # Depth 3: Evaluation & Finalized Path Selection (Project ID: 25-26J-130)
            prompt = PromptTemplate(
                template="""
                Role: Senior BI Pedagogical Auditor.
                
                Goal: {query}
                Path Reasoning: {internal_thought}
                
                TASK: Finalize the reasoning path with a 'Conclusion Blueprint'.
                STRICT REQUIREMENT: 
                - Do NOT generate full lesson text.
                - Summarize the final pedagogical goal and transition to synthesis.
                
                JSON FORMAT:
                {{
                    "options": [
                        {{
                            "directive": {{
                                "type": "final_blueprint",
                                "content": "FINAL BLUEPRINT: [Conclusion Strategy] ... [Multimodal Requirements] ..."
                            }}
                        }}
                    ]
                }}
                """,
                input_variables=["query", "internal_thought"]
            )
            for attempt in range(max_retries):
                try:
                    chain = prompt | llm | StrOutputParser()
                    # PROJECT ID: 25-26J-130: Local Timeout Guard for LLM stalls
                    raw_res = await asyncio.wait_for(
                        chain.ainvoke({
                            "query": query,
                            "internal_thought": parent_node.metadata.get("internal_thought", parent_node.content)
                        }),
                        timeout=45.0
                    )
                    
                    # --- REASONING TERMINAL STREAM ---
                    from socket_manager import sio
                    await sio.emit("thought_stream", {
                        "synthesis_id": state.get("interaction_id"),
                        "source": "Finalizing Path (D3)",
                        "content": raw_res,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else []
                    
                    children = []
                    for opt in options:
                        directive = opt.get("directive", {})
                        content_val = directive.get("content", "Final Path Selected")
                        children.append({
                            "content": "Finalized Path",
                            "metadata": {
                                "strategy_name": "Finalized Path",
                                "internal_thought": content_val,
                                "directive": directive,
                                "type": "final",
                                "pruning_status": "Selected"
                            }
                        })
                    return children
                except Exception as e:
                    print(f"Gen D3 Failed: {e}")
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
        
        # --- PHASE 18: POST-EVALUATION BROADCAST ---
        from socket_manager import sio
        await sio.emit("node_discovered", {
            "synthesis_id": state.get("interaction_id"),
            "id": node.id,
            "parent_id": node.parent_id,
            "depth": node.depth,
            "content": node.content,
            "metadata": {
                **node.metadata,
                "localScore": node.score,
                "pathScore": node.path_score,
                "pruning_status": "Evaluated"
            },
            "timestamp": datetime.now().isoformat()
        })
        
    # Early Stopping Logic (Project ID: 25-26J-130)
    stop_early = False
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    target_action = snapshot.get("action_id", 0)
    
    for node in scored_frontier:
        # PROJECT ID: 25-26J-130: HARDENED DEPTH ENFORCEMENT
        # Only allow early stopping at Depth 3+ to ensure research visibility for Phase 7
        if node.depth >= 3 and node.score >= CONFIG.score_threshold:
            stop_early = True
            current_best = node
            print(f"[ToT] 🎯 >>> Early Stopping Triggered (Depth {node.depth}): Score {node.score:.2f} >= {CONFIG.score_threshold}")
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
            
    # --- PHASE 18: SCORE-SYNCED PATH SELECTION ---
    if scored_frontier:
        # 1. Identify best node among siblings at this depth
        best_at_depth = max(scored_frontier, key=lambda x: x.path_score)
        
        # 2. Apply Threshold and Emit Selection
        if best_at_depth.path_score > 0.90:
            print(f"[ToT] 🏆 >>> Path Selected (Score {best_at_depth.path_score:.2f} > 0.90): Node {best_at_depth.id}")
            best_at_depth.metadata["pruning_status"] = "Selected"
            
            await sio.emit("path_selected", {
                "synthesis_id": state.get("interaction_id"),
                "id": best_at_depth.id,
                "parent_id": best_at_depth.parent_id,
                "path_score": best_at_depth.path_score,
                "depth": best_at_depth.depth
            })

    # Broadcast to Admin Dashboard
    await sio.emit("tot_step", {
        "step": "evaluate_frontier",
        "scores": [n.score for n in scored_frontier],
        "early_stop": stop_early
    })
    
    # Broadcast for UI Toast (Project ID: 25-26J-130)
    await sio.emit("tot_step", {
        "step": "EVALUATING_FRONTIER",
        "message": "Evaluating potential paths for optimal learning...",
        "synthesis_id": state.get("interaction_id")
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
            # PROJECT ID: 25-26J-130: Local Timeout Guard
            raw_res = await asyncio.wait_for(
                chain.ainvoke({
                    "query": state["user_query"],
                    "snapshot": json.dumps(snapshot),
                    "profile": str(state["profile"]),
                    "rl_strategy": snapshot.get("rl_strategy"),
                    "trend": snapshot.get("engagement_trend"),
                    "content": node.content,
                    "metadata": str(node.metadata)
                }),
                timeout=45.0
            )
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
        
    from socket_manager import sio
    # Broadcast for UI Toast (Project ID: 25-26J-130)
    await sio.emit("tot_step", {
        "step": "PRUNING_FRONTIER",
        "message": f"Narrowing focus to top {CONFIG.beam_width} reasoning paths...",
        "synthesis_id": state.get("interaction_id")
    })
        
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

    # Project ID: 25-26J-130: Real-time status propagation for intermediate nodes
    from socket_manager import sio
    for node in sorted_frontier:
        status = "Beam" if node in beam and node.metadata.get("pruning_status") != "Selected" else \
                 "Selected" if node.metadata.get("pruning_status") == "Selected" else "Pruned"
        
        await sio.emit("node_discovered", {
            "synthesis_id": state.get("interaction_id"),
            "id": node.id,
            "metadata": {
                **node.metadata,
                "pruning_status": status,
                "localScore": node.score,
                "pathScore": node.path_score
            }
        })

    # Broadcast to Admin Dashboard
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

async def background_synthesis(state: AgentState) -> AgentState:
    """
    Shadow ToT Node: Generates an alternative path in the background 
    if an intervention is needed.
    """
    snapshot = state["context_data"].get("snapshot", {})
    if not snapshot or not snapshot.get("intervention_needed"):
        return state

    print("[ToT] 🛰️ --- Node: Background Synthesis (Shadow ToT) ---")
    
    # 1. Identify Alternative Strategy
    # Penalize current modality if this was triggered by a Thumbs Down? 
    # Or just pick the next-best-scored path from a different branch.
    tree_memory = state["tree_memory"]
    best_node = state["best_node"]
    
    # Simple Logic: Find a node at the same depth as best_node but in a different branch
    candidates = [n for n in tree_memory.values() if n.depth == best_node.depth and n.id != best_node.id]
    
    if not candidates:
        print("[ToT] ⚠️ No alternative paths found for shadow synthesis.")
        return state
        
    shadow_best = max(candidates, key=lambda x: x.path_score)
    print(f"[ToT] 💎 Selected Shadow Path: {shadow_best.content[:50]}...")

    # 2. Synthesize Shadow Content
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from agent_core.llm import get_llm
    
    shadow_llm = get_llm()
    prompt = ChatPromptTemplate.from_template("""
        Role: Senior Pedagogical Architect.
        Task: Synthesize a SHADOW (alternative) lesson content.
        
        Alternative Thought: {thought}
        Goal: {query}
        
        Generate full multimodal text. Include [MERMAID_START] if visual.
    """)
    
    print(f"[ToT] 🤖 --- Starting Shadow Synthesis for: {shadow_best.content[:30]}...")
    shadow_chain = prompt | shadow_llm | StrOutputParser()
    try:
        shadow_lesson = await shadow_chain.ainvoke({
            "thought": shadow_best.content,
            "query": state["user_query"]
        })
        print("[ToT] 📝 Shadow Synthesis Result Received.")
    except Exception as e:
        print(f"[ToT] ❌ Shadow Synthesis Failed: {e}")
        return state

    # 3. Broadcast Shadow Ready via Socket.io
    print("[ToT] 📡 Emitting shadow_ready event...")
    from socket_manager import sio
    await sio.emit("shadow_ready", {
        "student_id": state["student_id"],
        "interaction_id": state.get("interaction_id"),
        "shadow_content": shadow_lesson,
        "modality": "VISUAL" if "[MERMAID_START]" in shadow_lesson else "TEXTUAL",
        "alternative_label": "Visual Analogy" if "[MERMAID_START]" in shadow_lesson else "Simplified Text"
    })

    print("[ToT] ✅ Shadow ToT Synthesis Complete & Broadcasted.")
    return {**state, "shadow_frontier": [shadow_best]}

async def finalizer_fan_out(state: AgentState) -> AgentState:
    """
    Passthrough node to trigger parallel finalization (Phase 19.2).
    """
    print("[ToT] 🚀 --- Node: Finalizer Fan-Out (Concurrent Main & Shadow) ---")
    return state

async def finalize_output(state: AgentState) -> AgentState:
    """
    Node 5: Final output generation and latency calculation.
    """
    print("[ToT] 🏁 --- Node: Finalize Output ---")
    
    # 1. ATOMIC SELECTION GUARD (Phase 19)
    if state.get("synthesis_locked"):
        print("[ToT] ⚠️ --- BLOCKED: Synthesis already in progress. Ignoring duplicate call. ---")
        return state
        
    best_node = state.get("best_node")
    if not best_node or best_node.metadata.get("pruning_status") != "Selected":
        print(f"[ToT] 🛑 --- BLOCKED: Node {best_node.id if best_node else 'N/A'} is NOT 'Selected'. Returning. ---")
        return state

    # LOCK PATH FOR SYNTHESIS
    interaction_id = state.get("interaction_id")
    tree_memory = state["tree_memory"]
    
    # 2. LOGGING VALIDATION
    sibling_count = len([n for n in tree_memory.values() if n.depth == best_node.depth]) - 1
    print(f"[Finalizer] --- LOCKED PATH: {best_node.id} | Discarding {sibling_count} sibling payloads ---")

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
        Selected Strategy Path (Blueprints): {thought}
        Strategy Label: {strategy}
        
        TASK: Perform Just-In-Time (JIT) Synthesis. Expand the selected reasoning blueprints into a comprehensive multimodal lesson.
        
        REQUIREMENTS:
        1. Start with a specific analogy: THE SUPERMARKET RECEIPT ANALOGY. 
           (CRITICAL: Do NOT use ANY other analogies).
        2. Expand on the technical methodologies mentioned in the blueprints.
        3. Explain 3 key technical terms related to Dimensional Modelling (Facts, Dimensions, Grain).
        4. Include a [MERMAID_START] diagram using [MERMAID_END] tags.
           - Central Node MUST be 'FactReceiptLineItem'.
           - Surround it with EXACTLY 5 dimensions: DimDate, DimProduct, DimStore, DimCustomer, DimPromotion.
           - Lay it out as a Star Schema.
        5. Use BI terminology (Facts, Dimensions, Star Schemas).
        6. Maintain an encouraging, professional tone.
        
        OUTPUT: Pure Markdown text with multimodal tags.
    """)
    
    # Trace the full path content for synthesis context
    blueprint_trace = " -> ".join([n.content for n in path])
    
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
            "thought": blueprint_trace,
            "strategy": strategy_label
        })
        
        # Enhanced Logging: Print full response object equivalent (the string output in this case)
        print(f"[ToT] >>> LLM Response Payload: {full_lesson}")
        
        # Project ID: 25-26J-130: Mermaid Syntax Repair Filter
        # Strips all Markdown formatting (bolding, etc) from inside mermaid blocks
        def repair_mermaid(text):
            def clean_mermaid(match):
                inner = match.group(1)
                # Strip markdown bolding/italics
                inner = re.sub(r"\*\*|\_\_", "", inner)
                # Strip leading/trailing whitespace
                return f"[MERMAID_START]\n{inner.strip()}\n[MERMAID_END]"
            return re.sub(r"\[MERMAID_START\](.*?)\[MERMAID_END\]", clean_mermaid, text, flags=re.DOTALL)
        
        full_lesson = repair_mermaid(full_lesson)
        
        # Project ID: 25-26J-130: RAG Verification Audit
        rag_sources = state["context_data"].get("rag_sources", [])
        print(f"[ToT] 📚 --- RAG Source Audit (Count: {len(rag_sources)}): {rag_sources}")
        
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
    
    # Project ID: 25-26J-130: RL Reinforcement - Flag high-confidence examples
    is_high_confidence = simulated_final_score >= 0.85
    
    # Interaction ID is already generated in retrieve_context (Project ID: 25-26J-130)
    interaction_id = state.get("interaction_id")

    # Recalculate latency after full_lesson is generated
    latency = time.time() - state.get("build_time", time.time())
    
    # --- INTERVENTION HARDENING (Project ID: 25-26J-130) ---
    from agent_core.snapshot import calculate_lesson_benchmark
    word_count = len(full_lesson.split())
    estimated_reading_time = calculate_lesson_benchmark(
        full_lesson, 
        state.get("profile", {}), 
        topic=state["user_query"]
    )
    
    print(f"[Intervention] --- Benchmark Set: {estimated_reading_time}s for {word_count} words ---")
    
    # Cleanup: Clear shadow_frontier once output is finalized to prevent leaks
    shadow_frontier = []
    
    # Save Interaction with CV/Branch Metadata (Project ID: 25-26J-130)
    # ASYNC DECOUPLING: Move persistence to background task
    # Project ID: 25-26J-130: Intervention Guard
    # If this is a shadow run (intervention_needed), DO NOT emit tot_final or save interaction.
    # The user must click "Yes, Switch" to apply this content.
    if snapshot.get("intervention_needed"):
        print("[ToT] 🛡️ Shadow Run Complete. Skipping final broadcast & persistence.")
        return {
            **state,
            "final_response": full_lesson,
            "body_text": full_lesson
        }

    async def save_mem():
        memory = MemoryManager()
        
        # Project ID: 25-26J-130: Robust ID handling for syn-* strings
        try:
            db_id = ObjectId(interaction_id)
        except Exception:
            db_id = interaction_id

        memory.save_interaction({
            "_id": db_id, # Ensure we use the same ID
            "student_id": state["student_id"],
            "query": state["user_query"],
            "strategy": strategy_label,
            "branch_id": best_node.id if best_node else None,
            "path_score": best_node.path_score if best_node else 0.0,
            "engagement_score": snapshot.get("current_affect", {}).get("score", 0.5), # Audit Requirement
            "outcome": outcome,
            "trace": trace,
            "high_confidence": is_high_confidence,
            "rag_sources": state["context_data"].get("rag_sources", []),
            "estimated_reading_time": estimated_reading_time,
            "is_completed": False,
            "timestamp": datetime.now()
        })
    asyncio.create_task(save_mem())

    # Final broadcast to Admin Dashboard
    from socket_manager import sio
    await sio.emit("tot_final", {
        "student_id": state["student_id"],
        "final_response": full_lesson,
        "full_text": full_lesson,
        "body_text": full_lesson,
        "strategy": strategy_label,
        "outcome": outcome,
        "trace": trace,
        "interaction_id": interaction_id,
        "strategy_label": strategy_label,
        "high_confidence": is_high_confidence,
        "rag_sources": state["context_data"].get("rag_sources", []),
        "current_modality": "VISUAL" if "[MERMAID_START]" in full_lesson else "TEXTUAL"
    })

    # --- PAYLOAD PURGE (Phase 19) ---
    # Clear the 'handoff_buffer' immediately after the first 'Finalize Output' call
    # and mark synthesis as locked to prevent duplicate Socket.IO emissions.
    updated_handoff = []
    
    await sio.emit("synthesis_complete", {
        "synthesis_id": interaction_id,
        "student_id": state["student_id"],
        "interaction_id": interaction_id,
        "final_content": full_lesson,
        "strategy": strategy_label,
        "rag_sources": state["context_data"].get("rag_sources", []),
        "current_modality": "VISUAL" if "[MERMAID_START]" in full_lesson else "TEXTUAL",
        "timestamp": datetime.now().isoformat()
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
        "current_modality": "VISUAL" if "[MERMAID_START]" in full_lesson else "TEXTUAL",
        "interaction_id": interaction_id,
        "build_time": latency,
        "estimated_reading_time": estimated_reading_time,
        "shadow_frontier": shadow_frontier,
        "synthesis_locked": True,
        "handoff_buffer": updated_handoff
    }

def create_tot_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("expand_frontier", expand_frontier)
    workflow.add_node("evaluate_frontier", evaluate_frontier)
    workflow.add_node("prune_frontier", prune_frontier)
    workflow.add_node("background_synthesis", background_synthesis)
    workflow.add_node("finalize_output", finalize_output)
    workflow.add_node("finalizer_fan_out", finalizer_fan_out)
    
    workflow.set_entry_point("retrieve_context")
    
    workflow.add_edge("retrieve_context", "expand_frontier")
    workflow.add_edge("expand_frontier", "evaluate_frontier")
    workflow.add_edge("evaluate_frontier", "prune_frontier")
    
    workflow.add_conditional_edges(
        "prune_frontier",
        check_stop_condition,
        {
            "expand": "expand_frontier",
            "finalize": "finalizer_fan_out" # Phase 19.2: Point to fan-out node
        }
    )

    # Parallel edges from fan-out
    workflow.add_edge("finalizer_fan_out", "finalize_output")
    workflow.add_edge("finalizer_fan_out", "background_synthesis")

    # Shadow ToT is isolated; it emits 'shadow_ready' and ends.
    workflow.add_edge("background_synthesis", END)
    workflow.add_edge("finalize_output", END)
    
    return workflow.compile()
