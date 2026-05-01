# Agentic AI Core: Execution Methods & Data Mapping

This document details the internal technical execution methods of the EduSynth platform, specifically focusing on the Reinforcement Learning (RL) policies, Computer Vision (CV) data payloads, and the LangGraph-based agentic orchestration.

## 1. Current Policies Provided by the RL Agent

The RL agent in EduSynth does not strictly output the *content* of an intervention, but rather the *pedagogical policy action* that the generative layer must execute. The current policy space (action space) consists of the following vectors:

1.  **`Complexity Escalation`**: Increases the cognitive demand of the content. This is triggered during "Flow" states when the system detects high comprehension velocity. It results in introducing advanced corollaries or harder problem sets.
2.  **`Scaffold Degradation`**: Reduces supportive structures. Triggered when mastery is approaching, removing step-by-step hints and forcing the student to rely on their own synthesized knowledge.
3.  **`Scaffold Injection`**: Instantly provides structural support. Triggered during "Frustration" or "High Confusion" states. It breaks a complex problem into smaller, micro-stepped milestones.
4.  **`Semantic Reframing`**: Alters the perspective or analogy used to explain a concept without changing the core knowledge, usually triggered when persistent "Confusion" is detected despite multiple attempts to digest standard text.
5.  **`Interactive Branching`**: Shifts from passive reading/listening to active recall. Triggered during "Attentional Decay" (Boredom/Gaze Drift). It forces a micro-quiz or Socratic interaction to regain focus.
6.  **`Modality Shift (Visual/Text/Audio)`**: Changes the primary presentation medium based on calculated *Modality Bias* or persistent friction in the current modality.

## 2. Computer Vision (CV) Data Types & Schemas

The 1.5s 'Biometric Heartbeat' captures three core modalities natively on the client via OpenCV and MediaPipe. The raw visual frames are immediately discarded; only abstracted numerical vectors are sent to the backend.

### Data Types Extracted:
*   **Emotion (Affective State):** Categorical classifications (Neutral, Flow, Confusion, Frustration, Boredom) paired with continuous Valence (negative/positive) and Arousal (low/high) values.
*   **Gaze (Attentional Focus):** Screen boundary tracking, quadrant fixation, fixation duration, and saccade velocity (rapid eye movement indicating reading or searching).
*   **Posture (Physical Engagement):** Shoulder alignment, head tilt, and distance from the screen. These serve as strong correlated indicators of fatigue or intense focus.

### Example JSON Payload (The Biometric Heartbeat)
When the frontend transmits the 1.5s interval data to the `FastAPI` ingestion endpoint, it structurally resembles the following JSON representation:

```json
{
  "timestamp": "2026-04-03T11:26:00Z",
  "session_id": "usr_992_sess_44",
  "module_id": "cs101_data_structures",
  "biometric_heartbeat": {
    "emotion": {
      "primary_state": "confusion",
      "confidence_score": 0.87,
      "multidimensional_affect": {
        "valence": -0.4,
        "arousal": 0.6
      }
    },
    "gaze": {
      "on_screen": true,
      "focus_target": "UI_quadrant_2",
      "fixation_duration_ms": 1200,
      "saccade_rate": "high_erratic"
    },
    "posture": {
      "alignment": "leaning_forward",
      "head_tilt_degrees": 15,
      "fatigue_indicator": 0.2
        }
  },
  "interaction_telemetry_delta": {
    "scroll_velocity": 0,
    "time_on_current_block_ms": 45000,
    "mouse_movement_entropy": 0.85
  }
}
```

## 3. Agentic AI Core Mapping & Execution Methods

The execution pipeline orchestrates how the JSON data above translates into a final, multimodal UI update via LangGraph. The pipeline consists of four primary state transitions:

### Phase 1: State Aggregation & Vectorization (The Ingestion Node)
1.  **Ingestion:** The FastAPI payload is received.
2.  **Aggregation:** The JSON data is merged with the user's historical state vector (e.g., previous 10 minutes of affect data).
3.  **Threshold Check:** If the state breaches an intervention threshold (e.g., `primary_state == 'confusion'` for > 3 consecutive heartbeats), the system triggers the RL Evaluation Node. 

### Phase 2: Policy Selection (The RL Evaluation Node)
1.  **Forward Pass:** The aggregated state vector is passed through the Reinforcement Learning model.
2.  **Reward Prediction:** The model evaluates which policy has the highest expected reward (Q-value) for returning the student to a "Flow" state. 
3.  **Output:** The RL model outputs a target policy directive, for example: `Policy -> Semantic Reframing`.

### Phase 3: Shadow ToT Simulation (The LangGraph Routing Node)
Once the RL policy dictates *what kind* of intervention is needed ("Semantic Reframing"), the Tree-of-Thought (ToT) agent figures out *how* to implement it optimally.
1.  **Branch Generation:** The agent uses Vertex AI to generate 3 alternative implementations of "Semantic Reframing" based on the current RAG context.
    *   *Path A:* Explain using an analogy regarding traffic flow.
    *   *Path B:* Explain using an analogy regarding water pipes.
    *   *Path C:* Synthesize a flowchart diagram mapping the logic.
2.  **Evaluation Protocol:** The agent executes an internal prompt asking: "Given the student is leaning forward (intense focus) but highly confused with high saccadic eye movement (frantically re-reading), which path reduces cognitive friction fastest?"
3.  **Selection:** The agent determines that *Path C* (Visual flowchart diagram) is the optimal modality shift to break the reading loop.

### Phase 4: JIT Synthesis & Delivery (The Execution Node)
1.  **Final Prompt Assembly:** Gemini 2.5 Flash is prompted with the RAG curriculum context, the ToT selected path (Path C), and formatting constraints.
2.  **Multimodal Synthesis:** The LLM generates the final output payload.
    ```json
    {
      "action": "inject_block",
      "type": "mermaid_diagram",
      "content": "graph TD;\n A[Raw Data] --> B[Processing]; ...",
      "supplementary_text": "Let's visualize this instead. Notice how..."
    }
    ```
3.  **Delivery:** The payload is pushed over WebSockets to the React.js frontend, rendering instantly and resolving the cognitive friction loop.
