# RL Engine Retraining Report (Project ID: 25-26J-130)

**Date:** 2026-03-08  
**Subject:** Transition to Student-Centric PPO Model with Multimodal CV Integration  
**Model ID:** `refined_pedagogical_policy.zip`

## 1. Executive Summary
The Reinforcement Learning (RL) engine has been upgraded from a basic heuristic DQN model to a robust **PPO (Proximal Policy Optimization)** architecture. This change was necessitated by the expansion of the observation space to include real-time Computer Vision (CV) metrics and deeper student personalization features.

## 2. Core Architectural Changes

### 2.1 Observation Space Expansion (14 Dimensions)
The `TutorEnv` was updated to ingest 14 distinct features to provide a high-fidelity state representation:
*   **Engagement Suite (CV):** Attention score, Confusion, Boredom.
*   **Inventory Features (CV):** `emotion_confidence`, `gaze_score` (forward vs. away), and `posture_score` (upright vs. slouched).
*   **Student Personalization:** `mastery_level` (0-1), `session_fatigue`, `avg_accuracy`, `avg_attention`, and `sessions_completed`.
*   **Module Context:** Current topic difficulty and `time_on_task`.

### 2.2 Pedagogical Action Policies (ACTION_MEANINGS 0-8)
We successfully implemented the full set of 9 "Student-Centric" actions:
1.  **Maintain_Current_Content (0):** Baseline progression.
2.  **Simplify_Explanation (1):** Remediation for high confusion.
3.  **Provide_Worked_Example (2):** Demonstration for low mastery.
4.  **Generate_Practice_Question (3):** Active assessment.
5.  **Switch_Learning_Mode (4):** Modality shift (e.g., text to visual).
6.  **Suggest_Break (5):** Wellbeing trigger (EAR < 0.18 or high fatigue).
7.  **Increase_Challenge (6):** Extension for high engagement + high mastery.
8.  **Review_Prerequisite (7):** Foundational remediation.
9.  **Prompt_Reflection (8):** Metacognitive pause.

### 2.3 Reward Function (R) Overhaul
The reward signal is now balanced to prioritize both learning outcomes and affective stability:
**R = (Engagement_Score * 0.4) + (Quiz_Accuracy * 0.4) + (Confidence_Bonus * 0.2)**

*   **Penalties:** Slight penalty (-0.1) for action 4 to prevent mode oscillation; penalty (-0.2) for 'away' gaze.

## 3. Implementation Details

### 3.1 Training Parameters
*   **Algorithm:** Stable-Baselines3 PPO.
*   **Timesteps:** 100,000.
*   **Learning Rate:** 3e-4.
*   **Batch Size:** 64.
*   **Entropy Coefficient:** Adjusted for exploration stability.

### 3.2 ToT Engine Integration
Modified `agent_core/graph.py` to utilize the `mastery_level` from the RL snapshot as a **tie-breaker** during the `prune_frontier` (Beam Search) phase, ensuring that pedagogical decisions are aligned with the student's long-term proficiency when path scores are identical.

## 4. Verification & Artifacts
*   **Trained Model:** [refined_pedagogical_policy.zip](../models/refined_pedagogical_policy.zip)
*   **Environment Logic:** [tutor_env.py](./src/env/tutor_env.py)
*   **Training Script:** [train_ppo.py](./src/train/train_ppo.py)

---
**Status:** ✅ RETRAINING COMPLETE (100k Epochs)  
**Lead:** AI Agentic Core Integration Team
