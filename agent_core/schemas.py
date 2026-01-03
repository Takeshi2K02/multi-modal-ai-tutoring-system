from typing import List, Dict, Optional, TypedDict, Any
from pydantic import BaseModel, Field
import uuid

class ThoughtNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    depth: int = 0
    content: str
    score: float = 0.0
    path_score: float = 0.0
    metadata: Dict[str, Any] = {}

    def __hash__(self):
        return hash(self.id)

class ToTConfig(BaseModel):
    max_depth: int = 2
    beam_width: int = 2
    branching_factor: int = 3
    score_threshold: float = 0.85
    max_nodes: int = 20

class AgentState(TypedDict):
    # Inputs
    student_id: str
    user_query: str
    
    # Internal State
    profile: Optional[Dict]
    context_data: Optional[Dict]
    
    frontier: List[ThoughtNode]
    tree_memory: Dict[str, ThoughtNode]
    best_node: Optional[ThoughtNode]
    
    # Output
    final_response: Optional[str]
    reasoning_trace: List[str]
