from typing import List, Dict, Optional, TypedDict, Any
from pydantic import BaseModel, Field
import uuid


# RL Policy -> Allowed Execution Strategies Mapping
RL_ACTION_MAP = {
    0: {"name": "Simplify content", "allowed": ["step_by_step", "reduce_cognitive_load", "recap"]},
    1: {"name": "Add interactive example", "allowed": ["guided_practice", "mini_exercise", "gamified_prompt"]},
    2: {"name": "Provide hint", "allowed": ["socratic_hint", "visual_hint", "worked_example_hint"]},
    3: {"name": "Increase difficulty", "allowed": ["challenge_problem", "extension_task"]},
    4: {"name": "Revise topic", "allowed": ["concept_reframing", "prerequisite_review"]},
    5: {"name": "Encourage student", "allowed": ["motivational_feedback", "confidence_boost"]}
}

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
