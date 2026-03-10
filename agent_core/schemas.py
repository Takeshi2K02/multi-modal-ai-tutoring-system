from typing import List, Dict, Optional, TypedDict, Any
from pydantic import BaseModel, Field
import uuid


# RL Policy -> Allowed Execution Strategies Mapping (Project ID: 25-26J-130)
RL_ACTION_MAP = {
    0: {"name": "Maintain Current Content", "type": "baseline"},
    1: {"name": "Simplify Explanation", "type": "remediation"},
    2: {"name": "Provide Worked Example", "type": "demonstration"},
    3: {"name": "Generate Practice Question", "type": "assessment"},
    4: {"name": "Switch Learning Mode", "type": "modality_shift"},
    5: {"name": "Suggest Break", "type": "wellbeing"},
    6: {"name": "Increase Challenge", "type": "extension"},
    7: {"name": "Review Prerequisite", "type": "remediation"},
    8: {"name": "Prompt Reflection", "type": "metacognition"}
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
    mastery_level: float = 0.5    # 0.0 - 1.0 (Tie-breaker for ToT)
    session_fatigue: float = 0.0  # 0.0 - 1.0
    confidence: float = 0.5       # From emotion_conf
    action_id: int = 0            # RL Action (0-8)
    intervention_needed: bool = False

class AgentState(TypedDict):
    # Inputs
    student_id: str
    user_query: str
    
    # Internal State
    profile: Optional[Dict]
    context_data: Optional[Dict] # Now holds StudentStateSnapshot
    teaching_strategy: Optional[Dict] # RL Engine input
    student_preferences: Dict[str, float]
    strategy_blacklist: List[str]
    
    frontier: List[ThoughtNode]
    tree_memory: Dict[str, ThoughtNode]
    best_node: Optional[ThoughtNode]
    
    # Output
    final_response: Optional[str]
    body_text: Optional[str]        # Project ID: 25-26J-130
    visual_tags: List[str]          # Project ID: 25-26J-130
    reasoning_trace: List[str]
    build_time: float
    stop_early: bool
    selected_strategy_label: Optional[str]
    interaction_outcome: Optional[str]
    interaction_id: Optional[str]
    shadow_frontier: List[ThoughtNode]
    is_completed: bool
    estimated_reading_time: int
    
    # Phase 19: Atomic Synthesis Guards
    handoff_buffer: List[Dict[str, Any]]
    synthesis_locked: bool
