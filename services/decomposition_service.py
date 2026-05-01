from typing import List, Dict, Any, Optional
import json
import re
import uuid
from langchain_core.messages import HumanMessage, SystemMessage
from services.vector_factory import get_vector_db
from agent_core.llm import get_llm
from db.connection import get_db_connection

# Hardcoded syllabus for Linear Algebra (as requested in MVP)
LINEAR_ALGEBRA_SYLLABUS = [
    "Vectors & Geometry", "Matrix Operations", "Linear Systems", 
    "Determinants", "Vector Spaces", "Linear Transformations",
    "Eigenvalues & Eigenvectors", "Orthogonality & SVD", "Diagonalization"
]

def decompose_goal(goal: str, collection_id: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Infers curriculum structure using VectorDB retrieval + Holistic LLM Structuring.
    (Project ID: 25-26J-130)
    """
    
    # Phase 21: RAG Isolation - Resolve collection_id if not provided
    if not collection_id and user_id:
        try:
            db = get_db_connection()
            if db is not None:
                # Try to find the latest session for this user to get the collection_id
                session = db.learning_sessions.find_one(
                    {"student_id": user_id},
                    sort=[("last_accessed_at", -1)]
                )
                if session and "collection_id" in session:
                    collection_id = session["collection_id"]
                    print(f"[Decompose] Resolved collection_id from session: {collection_id}")
                else:
                    # Fallback to checking the latest plan
                    plan = db.learning_plans.find_one(
                        {"student_id": user_id},
                        sort=[("created_at", -1)]
                    )
                    if plan and "system_metadata" in plan and "collection_id" in plan["system_metadata"]:
                        collection_id = plan["system_metadata"]["collection_id"]
                        print(f"[Decompose] Resolved collection_id from plan: {collection_id}")
        except Exception as e:
            print(f"[Decompose] Error resolving collection_id: {e}")

    # 1. Retrieve Evidence from VectorDB
    vectordb = get_vector_db()
    rag_filter = {"collection_id": collection_id} if collection_id else None
    retrieved_docs = vectordb.search(goal, top_k=25, filter=rag_filter)
    
    # Fallback: If no results found with filter, try without filter (Global Search)
    if not retrieved_docs and rag_filter:
        print(f"[Decompose] No results with filter. Falling back to global search.")
        retrieved_docs = vectordb.search(goal, top_k=25, filter=None)
    
    # Initialize Response
    response = {
        "goal": goal,
        "collectionId": collection_id,
        "status": "NO_COVERAGE",
        "evidenceCoverage": 0.0,
        "outlineConfidence": 0.0,
        "toc": [],
        "gaps": [],
        "showStartButton": False,
        "startRoute": "/toc"
    }
    
    if not retrieved_docs:
        response["gaps"].append({
            "title": "No Content Found", 
            "gapType": "OUT_OF_SCOPE", 
            "reason": "VectorDB is empty or has no matching content."
        })
        return response

    # 2. Analyze Relevance
    top_scores = [d["score"] for d in retrieved_docs[:10]]
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
    response["evidenceCoverage"] = round(min(avg_score, 1.0), 2)
    
    if avg_score < 0.25:
        response["gaps"].append({
            "title": "Low Relevance",
            "gapType": "POSSIBLE_MISMATCH",
            "reason": f"Retrieved content seems unrelated to '{goal}'."
        })

    # 3. Holistic Curriculum Design (Issue 2)
    llm = get_llm()
    
    all_chunks_context = []
    for i, doc in enumerate(retrieved_docs):
        meta = doc.get("metadata", {})
        source = meta.get("lecture_title") or meta.get("source_file") or "General Reference"
        all_chunks_context.append({
            "id": i,
            "source": source,
            "text": doc.get("text", "")[:500] 
        })
    
    chunks_json = json.dumps(all_chunks_context)
    
    holistic_prompt = f"""
    You are a Lead Curriculum Architect for EduSynth, an agentic tutoring system.
    Goal: "{goal}"
    
    Retrieved Knowledge Chunks:
    {chunks_json}
    
    Task:
    1. Design a comprehensive, multi-module curriculum (aim for 4-7 modules) that logically decomposes the Goal.
    2. Each module must have a clear 'title' and a list of 'topics'.
    3. For each topic, map it to the relevant 'chunk_indices' from the provided list.
    4. Ensure the flow is pedagogical (from basics to advanced).
    
    Return strictly Valid JSON:
    {{
        "curriculum_title": "Professional Course Title",
        "modules": [
            {{
                "title": "Module Name",
                "topics": [
                    {{
                        "title": "Topic Name",
                        "chunk_indices": [0, 5, 12]
                    }}
                ]
            }}
        ]
    }}
    """
    
    final_toc = []
    try:
        struct_result = llm.invoke([HumanMessage(content=holistic_prompt)])
        struct_content = struct_result.content
        
        match = re.search(r'\{.*\}', struct_content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
        else:
            raise ValueError("No JSON found in LLM response")
            
        response["generatedTitle"] = parsed.get("curriculum_title", goal.title())
        
        for mod in parsed.get("modules", []):
            topic_children = []
            for topic in mod.get("topics", []):
                evidence_source_docs = set()
                evidence_top_chunks = []
                
                for c_idx in topic.get("chunk_indices", []):
                    if 0 <= c_idx < len(all_chunks_context):
                        chunk = all_chunks_context[c_idx]
                        evidence_source_docs.add(chunk["source"])
                        evidence_top_chunks.append({
                            "text": chunk["text"],
                            "score": retrieved_docs[c_idx].get("score", 0)
                        })
                
                if evidence_top_chunks:
                    topic_children.append({
                        "id": str(uuid.uuid4()),
                        "title": topic["title"],
                        "type": "TOPIC",
                        "evidence": {
                            "sourceDocs": list(evidence_source_docs),
                            "topChunks": evidence_top_chunks
                        },
                        "children": []
                    })
            
            if topic_children:
                final_toc.append({
                    "title": mod["title"],
                    "type": "LECTURE_GROUP",
                    "children": topic_children
                })
                
    except Exception as e:
        print(f"[Decompose] Holistic structuring failed: {e}")
        
    response["toc"] = final_toc

    # 4. Final Status Determination
    if response["evidenceCoverage"] > 0.3 and len(final_toc) >= 3:
        response["status"] = "GOOD"
        response["showStartButton"] = True
        response["outlineConfidence"] = 0.9
    elif final_toc:
        response["status"] = "OK"
        response["showStartButton"] = True
        response["outlineConfidence"] = 0.6
    else:
        response["status"] = "LOW"
        response["showStartButton"] = False
        response["outlineConfidence"] = 0.1

    return response
