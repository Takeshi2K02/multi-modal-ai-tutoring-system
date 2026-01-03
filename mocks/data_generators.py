import random
from typing import Dict, Any

# Deterministic default values
DEFAULT_STUDENT_ID = "alex_123"
DEFAULT_CV_STATE = "neutral"
DEFAULT_STRATEGY = "visual_aids"

def get_mock_student_profile(student_id: str = DEFAULT_STUDENT_ID, randomized: bool = False) -> Dict[str, Any]:
    """
    Returns a mock student profile.
    Deterministic by default (returns "Alex").
    If randomized=True, returns variations.
    """
    if not randomized:
        return {
            "student_id": student_id,
            "name": "Alex",
            "age": 16,
            "learning_style": "visual",
            "interests": ["space", "video games", "coding"],
            "current_knowledge_level": {
                "math": "intermediate",
                "physics": "beginner"
            }
        }
    
    # Simple randomized variations
    names = ["Alex", "Sam", "Jordan", "Taylor"]
    styles = ["visual", "auditory", "kinesthetic"]
    return {
        "student_id": student_id,
        "name": random.choice(names),
        "age": random.randint(14, 18),
        "learning_style": random.choice(styles),
        "interests": ["music", "sports", "science"],
        "current_knowledge_level": {"math": "beginner"}
    }

def get_mock_cv_inputs(randomized: bool = False, state: str = DEFAULT_CV_STATE) -> Dict[str, Any]:
    """
    Simulates inputs from the Computer Vision system (engagement, emotion).
    'state' can be: 'neutral', 'confused', 'bored', 'excited'.
    """
    # Deterministic mapping for states
    state_map = {
        "neutral": {"engagement_score": 0.5, "emotion": "neutral", "attention_level": "medium"},
        "confused": {"engagement_score": 0.7, "emotion": "confused", "attention_level": "high"}, # Confused often means trying to understand
        "bored": {"engagement_score": 0.2, "emotion": "bored", "attention_level": "low"},
        "excited": {"engagement_score": 0.9, "emotion": "happy", "attention_level": "high"}
    }

    if not randomized and state in state_map:
        return state_map[state]
    
    # Randomized fallback
    return {
        "engagement_score": round(random.random(), 2),
        "emotion": random.choice(["neutral", "confused", "bored", "happy"]),
        "attention_level": random.choice(["low", "medium", "high"])
    }

def get_mock_rl_strategy(randomized: bool = False) -> str:
    """
    Simulates a suggestion from the Reinforcement Learning policy.
    """
    strategies = ["gamification", "socratic_method", "visual_aids", "analogy_based"]
    
    if not randomized:
        return "analogy_based" # Default hint
    
    return random.choice(strategies)
