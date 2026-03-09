from typing import List, Dict, Any
import json
from agent_core.strategy_taxonomy import StrategyType

class SynthesisService:
    @staticmethod
    def get_pruned_strategies(action_id: int) -> List[str]:
        """
        Action-Guided Pruning: Returns a subset of allowed StrategyTypes based on RL action.
        """
        # Default: All strategies allowed
        all_strategies = [s.value for s in StrategyType]
        
        # Action-specific pruning logic (Project ID: 25-26J-130)
        pruning_map = {
            1: ["analogy", "step_by_step", "visual_explanation"], # Simplify_Explanation
            2: ["step_by_step", "scaffolded_demo", "visual_explanation"], # Worked_Example
            3: ["concept_check", "knowledge_retrieval"], # Practice_Question
            4: ["visual_explanation", "interactive_demo"], # Switch_Learning_Mode
            5: ["mindful_reset", "breather"], # Suggest_Break
            6: ["advanced_application", "complexity_tuning", "extension"], # Increase_Challenge
            7: ["socratic_hint", "concept_check"], # Review_Prerequisite
            8: ["empathetic_correction", "metacognition"] # Prompt_Reflection
        }
        
        return pruning_map.get(action_id, all_strategies)

    @staticmethod
    def get_expansion_prompt(depth: int, context: Dict[str, Any]) -> str:
        """
        Returns optimized prompts for Node 2 based on depth and RL action constraints.
        """
        action_id = context.get("action_id", 0)
        strategies = SynthesisService.get_pruned_strategies(action_id)
        
        if depth == 1:
            return f"""
            Role: Senior BI Architect mentor. 
            Goal: Identify {context.get('k', 2)} targeted teaching strategies.
            RL Action Constraint: {context.get('rl_strategy', 'General')} (ID: {action_id})
            Allowed Strategies: {', '.join(strategies)}
            
            Pruning Rules: 
            - If action is 'Simplify', DO NOT suggest 'Increase Challenge'.
            - Focus strictly on grounded evidence from RAG context.
            
            JSON format: {{ "options": [ {{ "label": "...", "strategy_type": "...", "approach": "..." }} ] }}
            """
        
        # Preference Injection (Project ID: 25-26J-130)
        preferences = context.get("student_preferences", {})
        pref_instruction = ""
        if preferences.get("visual", 0) > 0.7:
            pref_instruction = "\nPRIORITIZE: Mermaid.js diagrams and visual analogies over dense paragraphs."
        elif preferences.get("interactive", 0) > 0.7:
            pref_instruction = "\nPRIORITIZE: Design Challenges and interactive simulations."

        strategy_fallback = ""
        if "analogy" in strategies:
            strategy_fallback = """
            SPECIAL CONSTRAINT (Analogy): If using the 'analogy' strategy, you MUST provide:
            1. At least 250 words of descriptive text.
            2. At least one structure diagram using [MERMAID_START] and [MERMAID_END] tags.
            """

        return f"""
        Role: Senior BI Architect.
        Task: Synthesize high-quality pedagogical content anchored in BI terminology.{pref_instruction}{strategy_fallback}
        Requirement: Include Mermaid diagrams if structure is complex.
        Format: JSON with 'directive' object containing 'type', 'content', and optional 'quiz'/'challenge'.
        """

synthesis_service = SynthesisService()
