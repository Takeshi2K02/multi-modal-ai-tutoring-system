import random
from typing import Dict, List, Any, Optional
from agent_core.schemas import RL_ACTION_MAP

class PedagogicalAgent:
    """
    Core RL engine for pedagogical policy decision making.
    Bridges CV telemetry (Affect) to pedagogical actions.
    """
    
    def __init__(self, student_id: str):
        self.student_id = student_id
        # Weights for each action_id (0-8)
        self.base_weights = {i: 0.1 for i in RL_ACTION_MAP.keys()}

    def get_action_distribution(self, engagement_score: float, emotion: str, profile: Dict[str, Any], feedback_signal: Optional[float] = None) -> Dict[str, float]:
        """
        Calculates a real-time probability distribution across all pedagogical actions.
        Project ID: 25-26J-130
        """
        weights = self.base_weights.copy()
        emotion = emotion.lower()
        
        # 1. Modality-Based Weighting (from StudentProfile)
        pref = profile.get("preferred_modality", {"visual": 0.33, "textual": 0.33, "interactive": 0.34})
        
        # If student prefers visual, boost 'Provide Worked Example' (ID 2)
        if pref.get("visual", 0) > 0.4:
            weights[2] += 0.2
            
        # If student prefers interactive, boost 'Generate Practice Question' (ID 3)
        if pref.get("interactive", 0) > 0.4:
            weights[3] += 0.2

        # 2. Affect-Based Weighting
        if engagement_score < 0.45 or emotion in ["bored", "distracted"] or feedback_signal == -1.0:
            # Stagnation approaching or negative feedback -> Boost 'Simplify' (1), 'Switch Mode' (4), or 'Suggest Break' (5)
            weights[1] += 0.4 if feedback_signal == -1.0 else 0.3
            weights[4] += 0.2
            weights[5] += 0.1
            
        elif emotion == "confused":
            # Confusion -> High priority on 'Simplify' (1) and 'Review Prerequisite' (7)
            weights[1] += 0.4
            weights[7] += 0.3
            
        elif (engagement_score > 0.85 and emotion == "focused") or feedback_signal == 1.0:
            # High engagement or positive feedback -> Boost 'Increase Challenge' (6) and 'Prompt Reflection' (8)
            weights[6] += 0.2
            weights[8] += 0.2
            weights[0] += 0.2 # Boost Maintain if feedback is positive
        else:
            # Baseline -> Maintain (0)
            weights[0] += 0.3

        # 3. Normalize to 1.0
        total = sum(weights.values())
        normalized_weights = {RL_ACTION_MAP[i]["name"]: round(w / total, 2) for i, w in weights.items()}
        
        return normalized_weights

    def select_action(self, distribution: Dict[str, float]) -> Dict[str, Any]:
        """
        Selects the top action from the distribution for logging and execution.
        """
        top_name = max(distribution, key=distribution.get)
        confidence = distribution[top_name]
        
        # Find action_id from name
        action_id = 0
        for aid, meta in RL_ACTION_MAP.items():
            if meta["name"] == top_name:
                action_id = aid
                break
                
        return {
            "action_id": action_id,
            "policy_name": top_name,
            "confidence": confidence,
            "reasoning": f"Affect-driven policy alignment (Conf: {int(confidence*100)}%)"
        }
