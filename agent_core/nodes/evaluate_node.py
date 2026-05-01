import asyncio, json, time
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent_core.schemas import AgentState, ThoughtNode
from agent_core.llm import get_llm
from agent_core.tot_config import semaphore, extract_json_from_text, CONFIG
from db.connection import get_db_connection, get_profiles_collection
from socket_manager import sio

def heuristic_prune(branches: list, context: dict) -> list:
    """
    Pre-filter frontier nodes using cheap heuristic rules before any LLM call.
    Caps the candidate set to 3, reducing Vertex AI burst traffic at Depth 2.
    """
    snapshot = context.get("snapshot", {})
    if hasattr(snapshot, "dict"):
        snapshot = snapshot.dict()

    rules = [
        lambda b: not (
            b.metadata.get("strategy_type", "") == "deliver_quiz"
            and snapshot.get("quiz_tolerance", 1.0) < 0.3
        ),
        lambda b: not (
            b.metadata.get("strategy_type", "") == "suggest_video"
            and snapshot.get("topic_abstraction", 0.0) > 0.7
        ),
        lambda b: not (
            b.metadata.get("strategy_type", "") == "generate_diagram"
            and snapshot.get("visual_preference", 1.0) < 0.4
        ),
        lambda b: not (
            b.metadata.get("strategy_type", "") == "extend_explanation"
            and snapshot.get("composite_engagement", 0.0) > 0.7
        ),
    ]
    pruned = [b for b in branches if all(r(b) for r in rules)]
    # Cap at 3; never return an empty list
    return pruned[:3] if pruned else branches[:2]


async def _evaluate_branches_parallel(branches: list, state: AgentState, tree_memory: dict) -> tuple:
    """
    Prunes the frontier heuristically, then scores survivors concurrently.
    Concurrency is capped by the module-level semaphore (tot_config.semaphore=3).
    Returns (scored_nodes_list, clean_scores).
    """
    context = state.get("context_data", {})
    pruned = heuristic_prune(branches, context)
    pruned_count = len(branches) - len(pruned)
    if pruned_count:
        print(f"[ToT] ✂️ Heuristic pruner removed {pruned_count} branch(es) "
              f"({len(branches)} → {len(pruned)})")

    tasks = [_score_node_content(state, b, tree_memory) for b in pruned]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    clean_scores = [s if isinstance(s, float) else 0.0 for s in results]
    return pruned, clean_scores


async def evaluate_frontier(state: AgentState) -> AgentState:
    """
    Node 3: Scores the new nodes in the frontier concurrently.
    Uses heuristic pruning + staggered dispatch to avoid Vertex AI 429 bursts.
    """
    print("[ToT] ⚖️ --- Node: Evaluate Frontier ---")
    frontier = state["frontier"]
    tree_memory = state["tree_memory"]

    if not frontier:
        return state

    eval_start = time.time()
    pruned, local_scores = await _evaluate_branches_parallel(frontier, state, tree_memory)
    logger_info = f"[ToT] Evaluate complete in {(time.time() - eval_start):.1f}s | Branches scored: {len(pruned)}"
    print(logger_info)
    
    scored_frontier = []
    current_best = state["best_node"]

    for node, local_score in zip(pruned, local_scores):
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

        # Ensure best_node is updated in the state to propagate deeper branches
        current_best = best_at_depth

        # 2. Apply Threshold or Depth selection
        # Change 1 (Project ID: 25-26J-130): depth >= 1 is now the terminal depth.
        if best_at_depth.path_score > 0.90 or best_at_depth.depth >= 1:
            print(f"[ToT] 🏆 >>> Path Selected (Score {best_at_depth.path_score:.2f} | Depth {best_at_depth.depth}): Node {best_at_depth.id}")
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

async def _score_node_content(state: AgentState, node: ThoughtNode, tree_memory: dict) -> float:
    """
    Scores the candidate path using Gemini with Exponential Backoff & Heuristic Fallback.
    Change 2 (Project ID: 25-26J-130): At depth >= 1 (the terminal depth after Change 1),
    uses a COMBINED scoring+synthesis prompt so the final LLM call in finalize_output
    can be skipped entirely, saving one full Vertex AI round-trip.
    (Project ID: 25-26J-130 | Issue 2 Fix)
    """
    import random
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    llm = get_llm()

    is_final_depth = node.depth >= 1  # depth 1 is terminal after Change 1

    if is_final_depth:
        # --- COMBINED SCORE + SYNTHESIS PROMPT ---
        # Produces both a numeric score and full lesson content in one LLM call.
        combined_prompt = PromptTemplate(
            template="""
Role: Senior Pedagogical Architect & Scoring Engine for Gemini 2.5 Flash.

Goal: {query}
Student State (Snapshot): {snapshot}
Student Profile: {profile}
RL Strategy: {rl_strategy} | Trend: {trend}

Candidate Path: "{content}"
Metadata: {metadata}

PART 1 — SCORING (0.0-1.0):
Evaluate this path on:
  1. Empathy Score (boost if deviation_alert is True in snapshot).
  2. Alignment with RL Strategy.
  3. Multi-modal Effectiveness for the current engagement trend.

PART 2 — SYNTHESIS:
Expand the selected strategy into a complete multimodal lesson.
REQUIREMENTS:
  1. Start with THE SUPERMARKET RECEIPT ANALOGY (no other analogies).
  2. Expand on the technical methodologies in the candidate path.
  3. Define 3 key BI terms: Facts, Dimensions, Grain.
  4. Include a [MERMAID_START] diagram with [MERMAID_END] tags.
     - Central node MUST be 'FactReceiptLineItem'.
     - Surround with EXACTLY 5 dimensions: DimDate, DimProduct, DimStore, DimCustomer, DimPromotion.
     - Star Schema layout.
  5. Use BI terminology throughout.
  6. Maintain an encouraging, professional tone.

OUTPUT FORMAT (STRICT — do not deviate):
SCORE: <float 0.0-1.0>
RATIONALE: <one sentence>
SYNTHESIS_PAYLOAD:
<full markdown lesson content here, including MERMAID block>
""",
            input_variables=["query", "snapshot", "profile", "rl_strategy", "trend", "content", "metadata"]
        )

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                async with semaphore:
                    chain = combined_prompt | llm | StrOutputParser()
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
                        timeout=30.0
                    )

                # --- Parse score ---
                score = 0.5
                score_match = __import__("re").search(r"SCORE:\s*([0-9.]+)", raw_res)
                if score_match:
                    try:
                        score = float(score_match.group(1))
                    except ValueError:
                        pass

                # --- Parse synthesis payload ---
                payload_match = __import__("re").search(
                    r"SYNTHESIS_PAYLOAD:\s*([\s\S]+)", raw_res
                )
                if payload_match:
                    synthesis_payload = payload_match.group(1).strip()
                    node.metadata["synthesis_payload"] = synthesis_payload
                    print(f"[ToT] 💾 Combined prompt: score={score:.2f}, "
                          f"payload_chars={len(synthesis_payload)} stored on node {node.id}")
                else:
                    print(f"[ToT] ⚠️ Combined prompt: no SYNTHESIS_PAYLOAD found in response for node {node.id}")

                return score

            except asyncio.CancelledError:
                print("[ToT] 🛑 >>> Scoring Cancelled: Graceful exit triggered.")
                raise
            except Exception as e:
                wait_time = base_delay * (2 ** attempt) + random.random()
                print(f"[ToT] ⚠️ Combined Scoring Failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time:.2f}s...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    pref = state.get("student_preferences", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
                    modality = node.metadata.get("strategy_type", "textual").lower()
                    fallback_score = 0.8 if pref.get(modality, 0) > 0.4 else 0.5
                    print(f"[ToT] ⚠️ Branch {node.id} scored via heuristic fallback ({fallback_score}) after {max_retries} LLM failures")
                    return fallback_score
        return 0.5

    else:
        # --- ORIGINAL SCORING-ONLY PROMPT (depth 0) ---
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

        max_retries = 3
        base_delay = 2.0

        for attempt in range(max_retries):
            try:
                async with semaphore:
                    chain = prompt | llm | StrOutputParser()
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
                        timeout=20.0
                    )
                    res = extract_json_from_text(raw_res)
                    return float(res.get("score", 0.5))
            except asyncio.CancelledError:
                print("[ToT] 🛑 >>> Scoring Cancelled: Graceful exit triggered.")
                raise
            except Exception as e:
                # Exponential Backoff with Jitter (Issue 2)
                wait_time = base_delay * (2 ** attempt) + random.random()
                print(f"[ToT] ⚠️ Scoring Failed (Attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time:.2f}s...")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    # Heuristic Fallback (Issue 2)
                    pref = state.get("student_preferences", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
                    modality = node.metadata.get("strategy_type", "textual").lower()
                    fallback_score = 0.8 if pref.get(modality, 0) > 0.4 else 0.5
                    print(f"[ToT] ⚠️ Branch {node.id} scored via heuristic fallback ({fallback_score}) after {max_retries} LLM failures")
                    return fallback_score
        return 0.5