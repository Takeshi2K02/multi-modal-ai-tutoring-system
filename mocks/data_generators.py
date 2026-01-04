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
    Simulates inputs from the Computer Vision system (Real Output Format).
    """
    # Deterministic mapping for states matches real model output structure
    state_map = {
        "neutral": {
            "timestamp": "2025-12-23T10:30:45Z",
            "emotion": "neutral",
            "emotion_conf": 0.85,
            "engagement_score": 0.50,
            "engagement_state": "passive",
            "gaze": "center",
            "posture": "neutral",
            "ocr_excerpt": "Reviewing quadratic formula...",
            "context_match": "algebra",
            "engagement_context_state": "neutral_listening"
        },
        "confused": {
            "timestamp": "2025-12-23T10:32:10Z",
            "emotion": "confused",
            "emotion_conf": 0.92,
            "engagement_score": 0.75, # High engagement but confused
            "engagement_state": "engaged_negative",
            "gaze": "screen_intense",
            "posture": "leaning_forward",
            "ocr_excerpt": "Wait, why is b squared?",
            "context_match": "quadratic_variables",
            "engagement_context_state": "confused_on_variables"
        },
        "bored": {
            "timestamp": "2025-12-23T10:45:00Z",
            "emotion": "bored",
            "emotion_conf": 0.88,
            "engagement_score": 0.20,
            "engagement_state": "disengaged",
            "gaze": "away",
            "posture": "slouched",
            "ocr_excerpt": "...",
            "context_match": "none",
            "engagement_context_state": "disengaged_boredom"
        },
        "excited": {
            "timestamp": "2025-12-23T10:55:00Z",
            "emotion": "happy",
            "emotion_conf": 0.95,
            "engagement_score": 0.95,
            "engagement_state": "engaged_positive",
            "gaze": "center",
            "posture": "upright_active",
            "ocr_excerpt": "I got the answer!",
            "context_match": "success_moment",
            "engagement_context_state": "high_engagement_success"
        }
    }

    if not randomized and state in state_map:
        return state_map[state]
    
    # Simple Randomized Fallback (keeps schema)
    return {
        "timestamp": "2025-12-23T11:00:00Z",
        "emotion": random.choice(["neutral", "confused", "bored", "happy"]),
        "emotion_conf": round(random.uniform(0.7, 0.99), 2),
        "engagement_score": round(random.random(), 2),
        "engagement_state": "unknown",
        "gaze": random.choice(["center", "away", "down"]),
        "posture": "varied",
        "ocr_excerpt": "Random simulation text",
        "context_match": "general",
        "engagement_context_state": "random"
    }

def get_mock_rl_strategy(randomized: bool = False, state_hint: str = "neutral") -> Dict[str, Any]:
    """
    Simulates a suggestion from the Reinforcement Learning policy (Real Output Format).
    """
    # Deterministic suggestions based on 'state_hint' if provided (implicit logic for demo)
    # The agent code currently calls this without args, but we can make it return a generally useful dict
    # or use the randomized flag to return variations.
    
    # Primary default (Analogy/General)
    default_rl = {
        "action_id": 1,
        "confidence": 0.85,
        "reasoning": "Student state is stable. Recommending analogy to reinforce concepts.",
        "timestamp": 1724159123.45
    }

    if not randomized:
        # In the real system, this would depend on the previous input. 
        # For the demo, we return a fixed 'Analogy' suggestion as the baseline hint
        # The ToT planner will then generate options around it.
        return default_rl
    
    # Variations
    variations = [
        {
            "action_id": 2,
            "confidence": 0.87,
            "reasoning": "Accuracy is low, providing guided practice.",
            "timestamp": 1724159123.45
        },
        {
            "action_id": 3,
            "confidence": 0.91,
            "reasoning": "Engagement is dropping. Gamification strategy recommended.",
            "timestamp": 1724159145.10
        }
    ]
    return random.choice(variations)