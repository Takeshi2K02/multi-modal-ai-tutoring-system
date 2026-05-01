import asyncio, re, json
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent_core.schemas import AgentState, ThoughtNode
from agent_core.llm import get_llm
from agent_core.tot_config import CONFIG, semaphore, extract_json_from_text
from socket_manager import sio

def heuristic_prune_branches(options: list, context: dict) -> list:
    """
    Pre-filters LLM-generated branch options before scoring.
    Eliminates branches that are obviously incompatible with current student state.
    """
    snapshot = context.get("snapshot", {})
    quiz_tolerance = snapshot.get("quiz_tolerance", 0.5)
    visual_preference = snapshot.get("visual_preference", 0.5)
    engagement = snapshot.get("composite_engagement", 0.5)
    
    filtered = []
    for opt in options:
        strategy_type = opt.get("strategy_type", "").lower()
        # Rule 1: Skip quiz if student quiz tolerance is low and engagement is not critically low
        if "quiz" in strategy_type and quiz_tolerance < 0.3 and engagement > 0.2:
            continue
        # Rule 2: Skip heavy video/external content if visual preference is low
        if "video" in strategy_type and visual_preference < 0.25:
            continue
        filtered.append(opt)
    
    # Safety: never return empty list — fall back to all options
    return filtered if filtered else options

async def expand_frontier(state: AgentState) -> AgentState:
    """
    Node 2: Expands the current frontier by generating thoughts.
    At depth > 0 only expands the winner from the previous evaluate cycle
    (state['best_node']) to avoid wasting LLM calls on pruned siblings.
    """
    frontier = state["frontier"]
    if not frontier:
        return state

    current_depth = frontier[0].depth
    next_depth = current_depth + 1

    print(f"[ToT] 🌿 --- Node: Expand Frontier (Depth {current_depth} -> {next_depth}) ---")

    # --- WINNER-ONLY EXPANSION (Project ID: 25-26J-130) ---
    # At depth > 0 the previous evaluate step has already selected best_node.
    # Only expand that winner; skip all sibling nodes to save LLM quota.
    best_node = state.get("best_node")
    if current_depth > 0 and best_node is not None:
        candidates = []
        for node in frontier:
            if node.id == best_node.id:
                print(f"[ToT] >>> Expanding WINNER only: '{node.content[:50]}' (Depth {current_depth})")
                candidates.append(node)
            else:
                print(f"[ToT] >>> Skipping non-winner: '{node.content[:50]}' (pruned before expand)")
    else:
        # Root expansion — no prior winner, expand all
        for node in frontier:
            print(f"[ToT] >>> Expanding parent node: '{node.content[:50]}...' (Depth {node.depth})")
        candidates = frontier

    tree_memory = state["tree_memory"].copy()

    # Generate children for winner candidates only
    tasks = [_generate_children_content(state, node, next_depth) for node in candidates]
    all_children_contents = await asyncio.gather(*tasks)
    
    new_frontier = []
    for node, children_contents in zip(candidates, all_children_contents):
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
    await sio.emit("tot_step", {
        "step": "EXPANDING_FRONTIER",
        "message": f"Expanding frontier to Depth {next_depth}...",
        "synthesis_id": state.get("interaction_id"),
        "depth": next_depth
    })

    return {**state, "frontier": new_frontier, "tree_memory": tree_memory}

async def _generate_children_content(state: AgentState, parent_node: ThoughtNode, target_depth: int) -> list:
    """
    Helper to generate content using LLM with Rate Limiting Semaphore.
    """
    profile = state["profile"]
    context = state["context_data"]
    query = state["user_query"]
    llm = get_llm()
    
    max_retries = 2
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
                        timeout=20.0
                    )
                    
                    # --- REASONING TERMINAL STREAM (Project ID: 25-26J-130) ---
                    await sio.emit("thought_stream", {
                        "synthesis_id": state.get("interaction_id"),
                        "source": "Expand Frontier (D1)",
                        "content": raw_res,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    res = extract_json_from_text(raw_res)
                    options = res.get("options", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])
                    
                    # Apply heuristic pre-filter
                    options = heuristic_prune_branches(options, context)
                    
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
                
                STRICT MERMAID REQUIREMENT (Issue 5):
                If the content requires a diagram, you MUST include a Mermaid block:
                - Use [MERMAID_START] and [MERMAID_END] tags.
                - Minimum 5 nodes.
                - Use 'graph TD' or 'sequenceDiagram'.
                - Example Skeleton: graph TD\n  A[Start] --> B[Process]\n  B --> C{{Decision}}\n  C -->|Yes| D[Result]\n  C -->|No| E[Retry]
                
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
                    async with semaphore:
                        chain = prompt | llm | StrOutputParser()
                        # PROJECT ID: 25-26J-130: Local Timeout Guard for LLM stalls
                        raw_res = await asyncio.wait_for(
                            chain.ainvoke({
                                "rag_evidence": context.get("rag_evidence", ""),
                                "strategy": parent_node.content, 
                                "approach": parent_node.metadata.get("approach", ""),
                                "query": query, "k": CONFIG.branching_factor
                            }),
                            timeout=20.0
                        )
                    
                    # --- REASONING TERMINAL STREAM (Project ID: 25-26J-130) ---
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
                        
                        # PAYLOAD INTEGRITY CHECK for BI Architecture/ETL/Schema (Issue 5)
                        bi_keywords = ['architecture', 'etl', 'schema', 'data warehouse', 'star schema', 'snowflake']
                        is_bi_technical = any(k in query.lower() for k in bi_keywords) or any(k in parent_node.content.lower() for k in bi_keywords)
                        
                        if is_bi_technical and target_depth == 2:
                            # Verify Mermaid tags are present and have content
                            mermaid_match = re.search(r"\[MERMAID_START\]([\s\S]+?)\[MERMAID_END\]", str(content_val))
                            if not mermaid_match or len(mermaid_match.group(1).strip()) < 10 or mermaid_match.group(1).count('-->') < 4:
                                print(f"[ToT] 🔄 Mermaid retry triggered for branch {parent_node.id}")
                                # Trigger ONE retry of the Mermaid section only
                                mermaid_retry_prompt = f"The following content is missing a valid Mermaid diagram (min 5 nodes). Please provide ONLY the [MERMAID_START]...[MERMAID_END] block for: {content_val}"
                                try:
                                    async with semaphore:
                                        from langchain_core.messages import HumanMessage
                                        retry_res = await asyncio.wait_for(
                                            llm.ainvoke([HumanMessage(content=mermaid_retry_prompt)]),
                                            timeout=15.0
                                        )
                                        new_mermaid = retry_res.content
                                        if "[MERMAID_START]" in new_mermaid:
                                            content_val = str(content_val) + "\n\n" + new_mermaid
                                        else:
                                            # Fallback if retry also fails
                                            content_val = str(content_val) + "\n\n[MERMAID_START]\ngraph TD\n  A[Data Source] --> B[ETL Layer]\n  B --> C[Data Warehouse]\n  C --> D[Analytics Layer]\n  D --> E[Visualization]\n[MERMAID_END]"
                                except Exception as e:
                                    print(f"[ToT] ⚠️ Mermaid retry failed: {e}")
                                    content_val = str(content_val) + "\n\n[MERMAID_START]\ngraph TD\n  A[Data Source] --> B[ETL Layer]\n  B --> C[Data Warehouse]\n  C --> D[Analytics Layer]\n  D --> E[Visualization]\n[MERMAID_END]"

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
                        timeout=20.0
                    )
                    
                    # --- REASONING TERMINAL STREAM ---
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
