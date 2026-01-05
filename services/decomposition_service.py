from typing import List, Dict, Any, Optional
import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from services.vector_factory import get_vector_db
from agent_core.llm import get_llm

# Hardcoded syllabus for Linear Algebra (as requested in MVP)
LINEAR_ALGEBRA_SYLLABUS = [
    "Vectors & Geometry", "Matrix Operations", "Linear Systems", 
    "Determinants", "Vector Spaces", "Linear Transformations",
    "Eigenvalues & Eigenvectors", "Orthogonality & SVD", "Diagonalization"
]

def decompose_goal(goal: str) -> Dict[str, Any]:
    """
    Infers curriculum structure using VectorDB retrieval + LLM Clustering.
    """
    
    # 1. Retrieve Evidence from VectorDB
    vectordb = get_vector_db()
    retrieved_docs = vectordb.search(goal, top_k=25)
    
    # Initialize Response
    response = {
        "goal": goal,
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

    # 2. Analyze Relevance (Score-based)
    # Chroma scores are distances or similarities. LocalVectorDB converts to similarity (0-1).
    top_scores = [d["score"] for d in retrieved_docs[:10]]
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
    response["evidenceCoverage"] = round(min(avg_score, 1.0), 2)
    
    # Heuristic: If widely irrelevant
    if avg_score < 0.25:
        response["status"] = "LOW"
        response["outlineConfidence"] = 0.2
        response["gaps"].append({
            "title": "Low Relevance",
            "gapType": "POSSIBLE_MISMATCH",
            "reason": f"Retrieved content seems unrelated to '{goal}' (Avg Score: {avg_score:.2f})."
        })
        # We proceed, but caution the user
    
    # 3. Group by Lecture/Source
    lectures = {}
    for i, doc in enumerate(retrieved_docs):
        meta = doc.get("metadata", {})
        # Prefer explicit lecture title, fallback to source file, then generic
        l_title = meta.get("lecture_title") or meta.get("source_file") or "General Reference"
        l_title = l_title.replace(".pdf", "").replace("Note", "Lecture").strip()
        
        if l_title not in lectures:
            lectures[l_title] = {"chunks": []}
        
        # Add index for reference
        lectures[l_title]["chunks"].append({
            "text": doc.get("text", "")[:400], # Trucate for context window safety
            "score": doc.get("score", 0),
            "page": meta.get("page_number", "?"),
            "original_index": i
        })

    # 4. LLM Structure Inference per Lecture
    final_toc = []
    llm = get_llm()
    
    for l_title, data in lectures.items():
        # Prepare Prompt
        chunks_text = "\n".join([f"[{idx}] {c['text']}..." for idx, c in enumerate(data["chunks"])])
        
        prompt = f"""
        You are a Curriculum Designer.
        Goal: "{goal}"
        Document: "{l_title}"
        
        Excerpts from Document:
        {chunks_text}
        
        Task:
        1. Identify the Main Topics covered in these excerpts relevant to the Goal.
        2. Group the chunks under these topics.
        3. Infer logical Subtopics if applicable.
        4. Ignore unrelated noise.

        Return strictly Valid JSON:
        {{
            "topics": [
                {{
                    "title": "Topic Name",
                    "subtopics": ["Subtopic 1", "Subtopic 2"],
                    "chunk_indices": [0, 2] 
                }}
            ]
        }}
        """
        
        try:
            # Synchronous LLM call
            result = llm.invoke([HumanMessage(content=prompt)])
            content = result.content
            
            # Robust JSON Extraction
            try:
                # Try to find JSON object between braces
                match = re.search(r'\{.*\}', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    parsed = json.loads(json_str)
                else:
                     raise ValueError("No JSON found in response")
            except json.JSONDecodeError:
                 # Last resort: try to clean common markdown issues
                 clean = content.replace("```json", "").replace("```", "").strip()
                 parsed = json.loads(clean)

            # Construct Hierarchy
            topic_children = []
            for topic in parsed.get("topics", []):
                
                # Gather evidence for this topic
                evidence_source_docs = set()
                evidence_top_chunks = []
                
                for c_idx in topic.get("chunk_indices", []):
                    if 0 <= c_idx < len(data["chunks"]):
                        chunk = data["chunks"][c_idx]
                        evidence_source_docs.add(f"Page {chunk['page']}")
                        evidence_top_chunks.append({
                            "text": chunk["text"],
                            "score": chunk["score"]
                        })
                
                # If no chunks assigned, skip (hallucination guard)
                if not evidence_top_chunks:
                    continue

                topic_children.append({
                    "title": topic["title"],
                    "type": "TOPIC",
                    "evidence": {
                        "sourceDocs": list(evidence_source_docs),
                        "topChunks": evidence_top_chunks
                    },
                    # Subtopics as purely metadata for now, or nested nodes?
                    # The visualizer expects 'children', so we can nest them or just list them in title
                    "children": [] 
                })
            
            if topic_children:
                final_toc.append({
                    "title": l_title,
                    "type": "LECTURE_GROUP",
                    "evidence": {"sourceDocs": [f"{len(data['chunks'])} excerpts"], "topChunks": []},
                    "children": topic_children
                })
                
        except Exception as e:
            print(f"LLM Structuring failed for {l_title}: {e}")
            # Fallback: Just list the lecture
            final_toc.append({
                "title": l_title,
                "type": "LECTURE_GROUP_FALLBACK",
                "evidence": {"sourceDocs": [], "topChunks": []},
                "children": []
            })
            
    response["toc"] = final_toc

    # 5. Domain-Aware Gap Analysis
    # Only check for Linear Algebra gaps if the Goal mentions it
    is_linalg_goal = "linear algebra" in goal.lower()
    
    if is_linalg_goal:
        # Check coverage
        covered_text = json.dumps(final_toc).lower()
        for canonical in LINEAR_ALGEBRA_SYLLABUS:
            if canonical.lower() not in covered_text:
                response["gaps"].append({
                    "title": canonical,
                    "gapType": "PROBABLY_MISSING",
                    "reason": "Standard Linear Algebra topic not found in retrieval."
                })
    else:
        # Generic Gap check (future: use LLM to identify gaps in user's custom goal)
        pass

    # 6. Final Status Determination
    if response["evidenceCoverage"] > 0.4 and final_toc:
        response["status"] = "GOOD"
        response["showStartButton"] = True
        response["outlineConfidence"] = 0.85
    elif final_toc:
        response["status"] = "OK"
        response["showStartButton"] = True
        response["outlineConfidence"] = 0.6
    else:
        response["status"] = "LOW"
        response["outlineConfidence"] = 0.1

    return response
