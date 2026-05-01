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
    
    path = []
    curr = best_node
    while curr:
        path.append(curr)
        curr = tree_memory.get(curr.parent_id) if curr.parent_id else None
    path.reverse()
    
    trace = [f"[{n.depth}] {n.content} (Score: {n.path_score:.2f})" for n in path]
    
    # Map RL Action ID to Strategy Label (Project ID: 25-26J-130)
    snapshot = state["context_data"].get("snapshot", {})
    if hasattr(snapshot, "dict"): snapshot = snapshot.dict()
    
    action_id = snapshot.get("action_id", 0)
    strategy_label = RL_ACTION_MAP.get(action_id, {}).get("name", "Unknown Strategy").upper().replace(" ", "_")
    
    # Project ID: 25-26J-130: Mandatory LLM Synthesis Step
    # Expand the selected thought into a full multimodal lesson
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

    print(f"[Pipeline] 🌲 ToT Path Found: {strategy_label}")
    print(f"[Pipeline] 🧩 Evaluating branch: {best_node.id} (Score: {best_node.path_score:.2f})")
    print(f"[Pipeline] 🤖 Triggering Final Content Synthesis for {state['user_query']}...")

    # Change 2 (Project ID: 25-26J-130): Use pre-computed synthesis payload if available.
    # The combined score+synthesis prompt in _score_node_content stores the lesson
    # content on the winning node at depth >= 1, saving one full Vertex AI round-trip.
    precomputed_payload = best_node.metadata.get("synthesis_payload") if best_node else None

    try:
        if precomputed_payload:
            print("[Finalizer] Using pre-computed synthesis payload — LLM call skipped")
            full_lesson = precomputed_payload
        else:
            # Fallback: original synthesis LLM call (kept intact, not deleted).
            chain = synthesis_prompt | final_llm | StrOutputParser()
            full_lesson = await chain.ainvoke({
                "query": state["user_query"],
                "thought": blueprint_trace,
                "strategy": strategy_label
            }, timeout=20.0)

        print("[Pipeline] ✅ Initial content generated and ready for delivery")

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
    latency = time.time() - start_time
    
    # --- INTERVENTION HARDENING (Project ID: 25-26J-130) ---
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
        "shadow_frontier": shadow_frontier,
        "synthesis_locked": True,
        "handoff_buffer": updated_handoff,
        "last_phase_time": new_last_time
    }
