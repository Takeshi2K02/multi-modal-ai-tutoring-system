# System Architecture & Execution Flow

This system effectively implements a **Hybrid AI Architecture** that combines symbolic planning (**Tree of Thought**) with generative capabilities (**LLMs**) and multimodal context (**CV/RL signals**).

## 1. Execution Pipeline: How it Works
When a user selects a scenario (e.g., "Student is Confused") via the UI or CLI, the following pipeline executes:

1.  **Context Assembly (Data Aggregation)**
    *   **Student Profile (Real)**: The system queries **MongoDB Atlas** for the student's long-term history and traits (e.g., "Alex", Visual Learner).
    *   **Perceptual Input (Mocked)**: The system intentionally injects simulated **Computer Vision (CV)** data (e.g., `emotion="confused"`, `gaze="screen_intense"`) compliant with the real schema.
    *   **Policy Suggestion (Mocked)**: The system injects a simulated **Reinforcement Learning (RL)** hint (e.g., `action_id=2` -> "Scaffolded Breakdown").

2.  **Tree of Thought Planning (The "Brain")**
    *   **Phase 1: Strategy Generation (Depth 1)**: The LLM (Gemini or local Llama 3) analyzes the Context. It does *not* jump to an answer. Instead, it proposes `K` distinct high-level teaching strategies (e.g., "Visual Breakdown" vs. "Socratic Questioning").
    *   **Phase 2: Evaluation (The Critic)**: The LLM conditionally scores each strategy (0.0 - 1.0) against the signals.
        *   *Example*: If `emotion="confused"`, the model penalizes abstract strategies and rewards scaffolded ones.
    *   **Phase 3: Beam Search (Pruning)**: The system applies a "Beam Width" (e.g., Top 2), discarding low-scoring strategies to focus computing resources on promising paths.
    *   **Phase 4: Content Generation (Depth 2)**: The LLM generates the actual tutoring dialogue/explanation only for the surviving strategies.

3.  **Finalization & Interaction**
    *   The Agent selects the single best path (highest cumulative score).
    *   The final tutoring response is returned to the user.
    *   **Persistence**: The session interaction or significant state changes can be logged back to MongoDB (if enabled).

## 2. The Planning Mechanism (Tree of Thought)
Currently configured with:
*   **Root**: The explicit Learning Goal (e.g., "Teach Quadratic Formula").
*   **Branching Factor (k=3)**: Generates 3 options at each decision point.
*   **Beam Width (w=2)**: Keeps only the top 2 best distinct reasonings at each layer.
*   **Depth (d=2)**: Planned 2 steps ahead (Strategy -> Content).

## 3. Data Flow & Storage
| Data Type | Storage Location | Persistence | Role |
| :--- | :--- | :--- | :--- |
| **Student Profile** | **MongoDB Atlas** | **Permanent** | Defines *who* we are teaching (Personalization). |
| **Reasoning Graph** | **In-Memory (State)** | Transient | Stores the thousands of potential thoughts generated during planning. Cleared after response. |
| **Multimodal Signals** | **Input Vector** | Transient | Real-time context (CV/RL) provided at runtime for the specific turn. |

## 4. User Interface (The Visualizer)
The React-based UI is a **Transparency Tool**. It does not just show the answer; it renders the entire **Graph State**:
*   **Nodes**: Represent individual "Thoughts" or "Strategies".
*   **Edges**: Show the derivation path.
*   **Colors/Badges**: Indicate the Score assigned by the Evaluator (Green = High Confidence, Red = Low/Pruned).
*   **Purpose**: To verify that the AI is obeying the CV/RL signals and making logical decisions, rather than hallucinating.

## 5. Implementation Status (Mock vs. Real)

| Component | Status | Description |
| :--- | :--- | :--- |
| **Cognitive Core (LLM)** | **REAL** | Uses Google Gemini (`gemini-2.0`) or local Ollama (`llama3`). |
| **Memory (DB)** | **REAL** | Connected to live MongoDB Atlas via SSL. |
| **Planning Logic** | **REAL** | Full LangGraph implementation of ToT + Beam Search. |
| **Computer Vision (CV)** | *Mocked* | Returns static JSON matching the real deep-learning model's schema. |
| **RL Policy** | *Mocked* | Returns static JSON matching the real RL policy's schema. |
| **Visualizer** | **REAL** | Dynamic React Flow graph rendering actual agent state. |

**In Summary:**
The system is a fully functional **reasoning engine**. It is currently "dreaming" the sensory inputs (CV/RL) via mocks, but the *reasoning* it performs on those inputs is real, structured, and database-backed.
