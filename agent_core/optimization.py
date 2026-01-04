from typing import Dict, Any

def compute_outcome(prev_cv: Dict[str, Any], current_cv: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determines if the interaction was a 'success' or 'failure' based on CV signal changes.
    
    Heuristic:
    - If Engagement Score increases -> Success
    - If Engagement State moves from distinct/confusion to high -> Success
    - If Confusion persists -> Failure
    - If Frustration detected -> Failure
    """
    
    # Defaults
    success = True
    reason = "Maintained engagement"
    delta = 0.0
    
    # 1. Compare Engagement Scores (0.0 - 1.0)
    prev_score = prev_cv.get("engagement_score", 0.5)
    curr_score = current_cv.get("engagement_score", 0.5)
    
    score_delta = curr_score - prev_score
    delta = score_delta
    
    # 2. Check States
    curr_state = current_cv.get("engagement_state", "neutral")
    curr_emotion = current_cv.get("facial_expression", "neutral")
    
    # Negative Triggers
    if curr_state in ["distracted", "sleeping"] or curr_emotion in ["frustrated", "bored"]:
        success = False
        reason = f"Negative state detected: {curr_state}/{curr_emotion}"
        delta -= 0.2
        
    # Positive Triggers
    elif curr_state == "highly_engaged" or curr_emotion in ["happy", "surprised"]:
        success = True
        reason = f"Positive state detected: {curr_state}/{curr_emotion}"
        delta += 0.2
        
    # Delta Logic
    elif score_delta > 0.1:
        success = True
        reason = "Engagement increased"
    elif score_delta < -0.1:
        success = False
        reason = "Engagement dropped"
        
    return {
        "success": success,
        "delta": delta,
        "reason": reason
    }
