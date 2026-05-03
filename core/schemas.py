from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ScenarioRequest(BaseModel):
    scenario: str = "neutral" # "confused" | "bored" | "neutral"
    topic_title: Optional[str] = None
    topic_content: Optional[str] = None
    synthesis_id: Optional[str] = None
    session_id: Optional[str] = None # Issue 2: For collection_id resolution
    collection_id: Optional[str] = None # Phase 21: RAG Isolation
    student_id: Optional[str] = None

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    meta: Dict[str, Any]
