from typing import List, Dict, Any, Set
from services.mock_vectordb import mock_vector_search

# Canonical Syllabus for Gap Detection (Linear Algebra MVP)
CANONICAL_TOPICS = {
    "topics": [
        "Vectors & Geometry", 
        "Matrix Operations", 
        "Linear Systems", 
        "Determinants", 
        "Vector Spaces", 
        "Linear Transformations",
        "Eigenvalues & Eigenvectors", # Known Gap
        "Orthogonality & SVD",        # Known Gap
        "Diagonalization"             # Known Gap
    ]
}

def decompose_goal(goal: str) -> Dict[str, Any]:
    """
    Infers curriculum structure from VectorDB evidence (metadata or semantic).
    """
    
    # 1. Retrieve Evidence
    retrieved_docs = mock_vector_search(goal, top_k=25)
    
    # 2. Initialize Response
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
        response["gaps"].append({"title": "All Topics", "gapType": "OUT_OF_SCOPE", "reason": "No curriculum content found."})
        return response

    # 3. Infer Structure Strategy
    # Check metadata availability
    docs_with_meta = [d for d in retrieved_docs if d.get("metadata", {}).get("lecture_id")]
    metadata_ratio = len(docs_with_meta) / len(retrieved_docs)
    
    use_metadata_structure = metadata_ratio >= 0.7
    
    structured_toc = []
    
    if use_metadata_structure:
        # Organize by Lecture
        lectures = {}
        for doc in retrieved_docs:
            meta = doc.get("metadata", {})
            lid = meta.get("lecture_id", "Unsorted")
            ltitle = meta.get("lecture_title", "General Topics")
            
            if lid not in lectures:
                lectures[lid] = {
                    "id": lid, 
                    "title": f"{lid}: {ltitle}", 
                    "docs": [],
                    "score_sum": 0.0
                }
            lectures[lid]["docs"].append(doc)
            lectures[lid]["score_sum"] += doc["score"]
            
        # Sort by Lecture ID
        sorted_lids = sorted(lectures.keys())
        
        for lid in sorted_lids:
            lec = lectures[lid]
            # Create Children (Topics) within Lecture
            # For this MVP, we cluster docs inside the lecture by their 'title' or 'topic'
            # Simple approach: each Doc is a Subtopic Concept
            children = []
            for doc in lec["docs"]:
                children.append({
                    "title": doc["title"],
                    "evidence": {
                        "sourceDocs": [f"{lid} p.{doc['metadata'].get('page', '?')}"],
                        "topChunks": [{"text": doc["text"], "score": doc["score"]}]
                    }
                })
                
            structured_toc.append({
                "title": lec["title"],
                "type": "LECTURE_GROUP",
                "evidence": {
                    "sourceDocs": [f"{len(lec['docs'])} relevant chunks"],
                    "topChunks": []
                },
                "children": children
            })
            
        response["outlineConfidence"] = 0.9 # High confidence because structure existed
        
    else:
        # Fallback: Topic Clustering (Previous Logic)
        clusters = {}
        for doc in retrieved_docs:
            topic = doc.get("topic", "Uncategorized")
            if topic not in clusters:
                clusters[topic] = {"docs": []}
            clusters[topic]["docs"].append(doc)
            
        for topic, data in clusters.items():
            children = []
            for doc in data["docs"]:
                 children.append({
                    "title": doc["title"],
                    "evidence": {
                        "sourceDocs": ["Textbook/Handout"],
                        "topChunks": [{"text": doc["text"], "score": doc["score"]}]
                    }
                })
            structured_toc.append({
                "title": topic,
                "type": "TOPIC_CLUSTER",
                "evidence": {"sourceDocs": [], "topChunks": []},
                "children": children
            })
        response["outlineConfidence"] = 0.5 # Medium confidence (inferred)
        
    response["toc"] = structured_toc

    # 4. Coverage Calculation
    # Simple metric: Ratio of Canonical Topics found in retrieved set (if Linear Algebra)
    # Or just raw score aggregation
    # MVP: Let's use average retrieval score of the top 10 docs as a proxy for relevance coverage
    top_scores = [d["score"] for d in retrieved_docs[:10]]
    avg_score = sum(top_scores) / len(top_scores) if top_scores else 0
    # Normalize (assuming max score ~ 3.0 in our mock)
    response["evidenceCoverage"] = min(avg_score / 1.5, 1.0) 
    response["evidenceCoverage"] = round(response["evidenceCoverage"], 2)

    # 5. Gap Detection
    # Using Canonical List again
    covered_text = " ".join([d["title"] + " " + d.get("topic", "") for d in retrieved_docs])
    for canonical in CANONICAL_TOPICS["topics"]:
        if canonical not in covered_text: # Simple keyword check
            response["gaps"].append({
                "title": canonical,
                "gapType": "PROBABLY_MISSING",
                "reason": "Topic expected in Linear Algebra but retrieved zero evidence."
            })
            
    # 6. Final Status
    if response["evidenceCoverage"] > 0.4:
        response["status"] = "GOOD"
        response["showStartButton"] = True
    elif response["evidenceCoverage"] > 0.1:
        response["status"] = "OK"
        response["showStartButton"] = True
    else:
        response["status"] = "LOW"
        response["showStartButton"] = False
        
    return response
