from typing import List, Dict, Optional, TypedDict, Any
from pydantic import BaseModel, Field
import uuid


# RL Policy -> Allowed Execution Strategies Mapping
RL_ACTION_MAP = {
    0: {"name": "Provide hint", "allowed": ["socratic_hint", "visual_hint", "worked_example_hint"]},
    1: {"name": "Worked example", "allowed": ["step_by_step", "demonstration", "scaffolded_demo"]},
    2: {"name": "Practice quiz", "allowed": ["mini_quiz", "concept_check", "knowledge_retrieval"]},
    3: {"name": "Challenge problem", "allowed": ["advanced_application", "problem_solving", "extension"]},
    4: {"name": "Modality shift", "allowed": ["video_to_interactive", "text_to_visual", "hands_on"]},
    5: {"name": "Short break", "allowed": ["mindful_reset", "breather", "topic_switch"]},
    6: {"name": "Personalized feedback", "allowed": ["empathetic_correction", "constructive_critique"]},
    7: {"name": "Adaptive difficulty", "allowed": ["dynamic_scaffolding", "complexity_tuning"]}
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

class StudentStateSnapshot(BaseModel):
    engagement_trend: str  # "declining", "stable", "improving"
    current_affect: Dict[str, Any]
    rl_strategy: str
    performance_summary: str
    deviation_alert: bool = False

class AgentState(TypedDict):
    # Inputs
    student_id: str
    user_query: str
    
    # Internal State
    profile: Optional[Dict]
    context_data: Optional[Dict] # Now holds StudentStateSnapshot
    teaching_strategy: Optional[Dict] # RL Engine input
    
    frontier: List[ThoughtNode]
    tree_memory: Dict[str, ThoughtNode]
    best_node: Optional[ThoughtNode]
    
    # Output
    final_response: Optional[str]
    reasoning_trace: List[str]
