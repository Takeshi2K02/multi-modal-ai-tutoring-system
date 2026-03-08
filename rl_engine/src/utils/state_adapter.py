def vision_to_rl_state(cv_output, history=None):
    """
    Convert CV module output → RL numeric state
    """

    attention = cv_output.get("engagement_score", 0.5)

    confusion = 0.7 if cv_output.get("emotion") == "confused" else 0.2

    boredom = 0.6 if cv_output.get("gaze") == "away" else 0.2

    difficulty = 0.5   # later from Agentic core

    recent_acc = history.get("recent_acc", 0.5) if history else 0.5

    time_on_task = history.get("time_on_task", 0.2) if history else 0.2

    return {
        "attention": attention,
        "confusion": confusion,
        "boredom": boredom,
        "difficulty": difficulty,
        "recent_acc": recent_acc,
        "time_on_task": time_on_task
    }