import asyncio, re, json, time
from datetime import datetime
from bson import ObjectId
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agent_core.schemas import AgentState, RL_ACTION_MAP
from agent_core.llm import get_llm
from agent_core.snapshot import calculate_lesson_benchmark
from memory.student_memory import MemoryManager
from socket_manager import sio

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
    await sio.emit("shadow_ready", {
        "student_id": state["student_id"],
        "interaction_id": state.get("interaction_id"),
        "shadow_content": shadow_lesson,
        "modality": "VISUAL" if "[MERMAID_START]" in shadow_lesson else "TEXTUAL",
        "alternative_label": "Visual Analogy" if "[MERMAID_START]" in shadow_lesson else "Simplified Text"
    })

    print("[ToT] ✅ Shadow ToT Synthesis Complete & Broadcasted.")
    return {**state, "shadow_frontier": [shadow_best]}

async def finalize_output(state: AgentState) -> AgentState:
    """
    Node 5: Final output generation and latency calculation.
    """
    # Fix 2: Move pre-computed payload check to the very top to skip all LLM work
    best_node = state.get("best_node")
    precomputed_payload = best_node.metadata.get("synthesis_payload") if best_node else None
    
    # Common variables needed for both paths
    interaction_id = state.get("interaction_id")
    tree_memory = state["tree_memory"]
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    
    # 1. ATOMIC SELECTION GUARD (Phase 19)
    if state.get("synthesis_locked"):
        print("[ToT] ⚠️ --- BLOCKED: Synthesis already in progress. Ignoring duplicate call. ---")
        return state
        
    if not best_node or best_node.metadata.get("pruning_status") != "Selected":
        print(f"[ToT] 🛑 --- BLOCKED: Node {best_node.id if best_node else 'N/A'} is NOT 'Selected'. Returning. ---")
        return state

    start_time = state.get("build_time", time.time())

    if precomputed_payload:
        print(f"[Finalizer] ✅ Using pre-computed synthesis payload for node {best_node.id} — skipping ALL LLM logic.")
        full_lesson = precomputed_payload
        trace = ["Pre-computed synthesis used."]
        
        # Determine strategy label
        action_id = snapshot.get("action_id", 0)
        strategy_label = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown Strategy").upper().replace(" ", "_")
        
        # Assign outcome metrics
        latency = time.time() - start_time
        initial_score = snapshot.get("current_affect", {}).get("score", 0.5)
        simulated_final_score = min(1.0, initial_score + 0.2) if best_node.path_score > 0.8 else initial_score
        outcome = "Improved" if simulated_final_score > initial_score else "Stable"
        is_high_confidence = simulated_final_score >= 0.85
        estimated_reading_time = state.get("estimated_reading_time", 30)
    else:
        print("[ToT] 🏁 --- Node: Finalize Output ---")
        
        # LOCK PATH FOR SYNTHESIS
        sibling_count = len([n for n in tree_memory.values() if n.depth == best_node.depth]) - 1
        print(f"[Finalizer] --- LOCKED PATH: {best_node.id} | Discarding {sibling_count} sibling payloads ---")

        path = []
        curr = best_node
        while curr:
            path.append(curr)
            curr = tree_memory.get(curr.parent_id) if curr.parent_id else None
        path.reverse()
        
        trace = [f"[{n.depth}] {n.content} (Score: {n.path_score:.2f})" for n in path]
        
        # Map RL Action ID to Strategy Label
        action_id = snapshot.get("action_id", 0)
        strategy_label = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown Strategy").upper().replace(" ", "_")
        
        # Project ID: 25-26J-130: Mandatory LLM Synthesis Step
        final_llm = get_llm()
        
        # Task 2: Pre-built Mermaid Integration
        prebuilt_mermaid = state["context_data"].get("prebuilt_mermaid")
        mermaid_instruction = f"Inject this EXACT Mermaid diagram: {prebuilt_mermaid}" if prebuilt_mermaid else "Include a [MERMAID_START] diagram with [MERMAID_END] tags as per requirements."

        synthesis_prompt = ChatPromptTemplate.from_template("""
            Role: Senior Pedagogical Architect.
            Context: {query}
            Selected Strategy Path (Blueprints): {thought}
            Strategy Label: {strategy}
            
            TASK: Perform Just-In-Time (JIT) Synthesis. Expand the selected reasoning blueprints into a comprehensive multimodal lesson.
            
            REQUIREMENTS:
            1. Start with THE SUPERMARKET RECEIPT ANALOGY. 
            2. Expand on the technical methodologies.
            3. Explain 3 terms: Facts, Dimensions, Grain.
            4. {mermaid_instruction}
            
            OUTPUT: Pure Markdown.
        """)
        
        blueprint_trace = " -> ".join([n.content for n in path])
        print("[ToT] 📝 --- Attempting Final Synthesis (Fallback) ---")
        
        try:
            chain = synthesis_prompt | final_llm.bind(thinking_config={"include_thoughts": False, "budget_tokens": 0}) | StrOutputParser()
            full_lesson = await chain.ainvoke({
                "query": state["user_query"],
                "thought": blueprint_trace,
                "strategy": strategy_label,
                "mermaid_instruction": mermaid_instruction
            }, timeout=25.0)

            print("[Pipeline] ✅ Content ready for delivery")
            def repair_mermaid(text):
                def clean_mermaid(match):
                    inner = match.group(1)
                    inner = re.sub(r"\*\*|\_\_", "", inner)
                    return f"[MERMAID_START]\n{inner.strip()}\n[MERMAID_END]"
                return re.sub(r"\[MERMAID_START\](.*?)\[MERMAID_END\]", clean_mermaid, text, flags=re.DOTALL)
            
            full_lesson = repair_mermaid(full_lesson)
            if not full_lesson or not isinstance(full_lesson, str) or len(full_lesson.strip()) == 0:
                raise ValueError("LLM returned empty body_text")
            
            initial_affect = snapshot.get("current_affect", {})
            initial_score = initial_affect.get("score", 0.5)
            simulated_final_score = min(1.0, initial_score + 0.2) if best_node and best_node.path_score > 0.8 else initial_score
            outcome = "Improved" if simulated_final_score > initial_score else "Stable"
            is_high_confidence = simulated_final_score >= 0.85
            latency = time.time() - start_time
            estimated_reading_time = calculate_lesson_benchmark(full_lesson, state.get("profile", {}), topic=state["user_query"])
                
        except Exception as e:
            print(f"Synthesis Failed: {e}")
            full_lesson = f"### 🧩 Fallback Lesson: Understanding {state['user_query']}\n\nTechnical hiccup occurred. {state['user_query']} is a key concept in BI."
            outcome = "Stable"
            is_high_confidence = False
            latency = 0
            estimated_reading_time = 30

    if snapshot.get("intervention_needed"):
        print("[ToT] 🛡️ Shadow Run Complete. Skipping final broadcast & persistence.")
        return {**state, "final_response": full_lesson, "body_text": full_lesson}

    async def save_mem():
        memory = MemoryManager()
        try:
            db_id = ObjectId(interaction_id)
        except Exception:
            db_id = interaction_id
        memory.save_interaction({
            "_id": db_id,
            "student_id": state["student_id"],
            "query": state["user_query"],
            "strategy": strategy_label,
            "branch_id": best_node.id if best_node else None,
            "path_score": best_node.path_score if best_node else 0.0,
            "engagement_score": snapshot.get("current_affect", {}).get("score", 0.5),
            "outcome": outcome,
            "trace": trace,
            "high_confidence": is_high_confidence,
            "rag_sources": state["context_data"].get("rag_sources", []),
            "estimated_reading_time": estimated_reading_time,
            "is_completed": False,
            "timestamp": datetime.now()
        })
    asyncio.create_task(save_mem())

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

    from agent_core.timing_utils import log_and_emit_progress
    new_last_time = await log_and_emit_progress(state, "synthesis_complete", "Synthesizing lesson")

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
        "shadow_frontier": [],
        "synthesis_locked": True,
        "handoff_buffer": updated_handoff,
        "last_phase_time": new_last_time
    }
