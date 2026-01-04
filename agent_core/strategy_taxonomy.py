from enum import Enum
from typing import Dict, Any

class StrategyType(str, Enum):
    VISUAL_EXPLANATION = "visual_explanation"
    SCAFFOLDED_STEPS = "scaffolded_steps"
    SOCRATIC_QUESTIONING = "socratic_questioning"
    WORKED_EXAMPLE = "worked_example"
    INTERACTIVE_PRACTICE = "interactive_practice"
    GAMIFIED_QUIZ = "gamified_quiz"
    ANALOGY_CONTEXTUAL = "analogy_contextual"
    RECAP_SUMMARIZE = "recap_summarize"
    MOTIVATIONAL_ENCOURAGEMENT = "motivational_encouragement"

# Metadata for UI display
STRATEGY_METADATA = {
    StrategyType.VISUAL_EXPLANATION: {"label": "Visual Explanation", "icon": "🖼️"},
    StrategyType.SCAFFOLDED_STEPS: {"label": "Step-by-Step", "icon": "👣"},
    StrategyType.SOCRATIC_QUESTIONING: {"label": "Socratic Q&A", "icon": "🤔"},
    StrategyType.WORKED_EXAMPLE: {"label": "Worked Example", "icon": "📝"},
    StrategyType.INTERACTIVE_PRACTICE: {"label": "Practice Problem", "icon": "✍️"},
    StrategyType.GAMIFIED_QUIZ: {"label": "Gamified Quiz", "icon": "🎮"},
    StrategyType.ANALOGY_CONTEXTUAL: {"label": "Real-world Analogy", "icon": "🌍"},
    StrategyType.RECAP_SUMMARIZE: {"label": "Summary", "icon": "📑"},
    StrategyType.MOTIVATIONAL_ENCOURAGEMENT: {"label": "Encouragement", "icon": "🌟"},
}

def get_strategy_label(st: StrategyType) -> str:
    return STRATEGY_METADATA.get(st, {}).get("label", st)
