# Agentic AI Core - Tree of Thought (ToT) System

A sophisticated AI Planning agent using Tree of Thought reasoning, Beam Search, and Multi-Depth expansion strategies.

## 🚀 Quick Start

### 1. Setup
```bash
# Create Virtual Env
python3 -m venv venv
source venv/bin/activate

# Install Dependencies (includes new Ollama support)
python3 -m pip install -r requirements.txt
```

### 2. Configure Provider
This system supports **Google Gemini (Cloud)** and **Ollama (Local)**.

**Option A: Context-Aware Default (Gemini)**
Create a `.env` file:
```ini
GOOGLE_API_KEY="your_api_key"
LLM_PROVIDER="gemini"
```

**Option B: Local Power (Ollama)**
1.  **Install Ollama**: [Download for Mac](https://ollama.com/download)
2.  **Pull Model**: `ollama pull llama3`
3.  **Configure `.env`**:
    ```ini
    LLM_PROVIDER="ollama"
    OLLAMA_MODEL="llama3"
    ```

### 3. Running the Application

To run the full multimodal system (Backend + Frontend):

#### **Backend (FastAPI)**
The backend handles the agentic reasoning and data persistence.
```bash
# Option A: Direct command
uvicorn server:app --reload --port 8000

# Option B: Use helper script (Mac/Linux)
chmod +x start_backend.sh
./start_backend.sh
```

#### **Frontend (React)**
The web interface for interacting with the agent.
```bash
cd web-ui
npm install # If first time
npm run dev
```

### 4. CLI Demo (Alternative)
Run a quick test in your terminal without the web UI:
```bash
python3 main.py
```

---

## 🏗️ Architecture

-   **Agent Core**: LangGraph workflow implementing `Expand -> Evaluate -> Prune` loop.
-   **LLM Factory**: `agent_core/llm.py` handles provider switching.
-   **Visualization**: React Flow based UI.

### Tree of Thought Logic
-   **Depth 0**: Root (User Query)
-   **Depth 1**: Strategy Generation (e.g., Socratic, Analogy)
-   **Depth 2**: Content Generation (Step-by-step breakdown)
-   **Beam Search**: Prunes low-scoring paths at each depth.
