from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel, Field
from datetime import datetime

class LearningGoal(BaseModel):
    topic: str
    difficulty: str = "intermediate"
    objectives: List[str] = []

class StudentProfile(BaseModel):
    student_id: str
    name: str
    age: int
    learning_style: str  # e.g., "visual", "auditory", "kinesthetic"
    interests: List[str]
    current_knowledge_level: Dict[str, str] = {} # topic -> level

class InteractionLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    student_id: str
    goal_id: str
    chosen_strategy: str
    scores: Dict[str, float]
    cv_state: str
    rl_hint: str
    response_text: str
    estimated_reading_time: int = 120 # Default 2 minutes
    is_completed: bool = False

class AgentState(TypedDict):
    # Inputs
    student_id: str
    user_query: str
    
    # Internal State
    profile: Optional[Dict]
    context_data: Optional[Dict] # CV, RL, Memory
    candidate_strategies: List[str]
    strategy_scores: Dict[str, float]
    selected_strategy_label: Optional[str]
    retries: int
    
    # Output
    final_response: Optional[str]
    reasoning_trace: List[str]
