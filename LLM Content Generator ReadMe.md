# LLM Content Generator & Project Setup Guide (Windows)

This guide describes how to set up the project environment and run the application on **Windows**, specifically focusing on the **LLM Content Generator** and **Lecture Note Upload** workflows.

## 1. Prerequisites
-   **Python 3.10+** (Ensure you check "Add Python to PATH" during installation)
-   **Node.js 18+** & **npm**
-   **Ollama** (for local LLM - [Download for Windows](https://ollama.com/download/windows)) or **Google Gemini API Key** (for cloud LLM)
-   **MongoDB Atlas** account (or use the default demo cluster provided in the code)
-   **Visual Studio C++ Build Tools** (Required for some Python packages like ChromaDB)

### 1.1 Ollama Configuration (Critical)
This project is configured to use the **Llama 3** model by default. You **MUST** pull this model before running the backend.

1.  Download and install Ollama from [ollama.com](https://ollama.com).
2.  Open your command prompt or PowerShell.
3.  Run the following command to download the model:
    ```powershell
    ollama pull llama3
    ```
4.  Keep the Ollama app running in the background (it serves the API at `localhost:11434`).

---

## 2. Backend Setup

### A. Environment Setup
1.  Navigate to the project root directory in Command Prompt or PowerShell.
2.  Create a virtual environment:
    ```powershell
    python -m venv venv
    ```
3.  Activate the virtual environment:
    *   **Command Prompt:**
        ```cmd
        venv\Scripts\activate.bat
        ```
    *   **PowerShell:**
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```
    *(If you get a permission error in PowerShell, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### B. Install Dependencies
Install all required Python packages.

```powershell
# Upgrade pip first
python -m pip install --upgrade pip

# Install from requirements
pip install -r requirements.txt

# Ensure critical dependencies are present
pip install fastapi uvicorn pypdf chromadb python-multipart langgraph
```

### C. Configure Environment Variables
Create a `.env` file in the root directory.

**Minimal `.env` Configuration:**
```ini
# Choose your LLM Provider: 'ollama' or 'gemini'
LLM_PROVIDER="ollama" 

# If using Ollama (Local)
OLLAMA_MODEL="llama3"

# If using Gemini (Cloud)
# GOOGLE_API_KEY="your_api_key_here"

# MongoDB Connection (Optional: Only if you want to override the default cluster)
# MONGO_URI="mongodb+srv://..."
```

---

## 3. Frontend Setup

Move to the `web-ui` directory and install JavaScript dependencies.

```powershell
cd web-ui
npm install
```

---

## 4. Running the Application

You will need **two terminal windows**.

### Terminal 1: Backend (FastAPI)
From the project root (ensure `venv` is active - you should see `(venv)` in your prompt):

```powershell
# From the root folder 'multimodal-ai-tutoring-system'
uvicorn server:app --reload --port 8000
```
*Wait for the log to say "Application startup complete".*

### Terminal 2: Frontend (React/Vite)
From the `web-ui` folder:

```powershell
cd web-ui
npm run dev
```
*Access the app at `http://localhost:5173/`.*

---

## 5. Workflow: Lecture Material Upload & Agent Core

### A. Uploading Lecture Notes (PDF)
1.  Open the web application.
2.  Click on the **"Upload"** button in the top navigation bar.
3.  Select your PDF lecture notes (e.g., "Linear_Algebra_Lec1.pdf").
4.  Click **"Start Ingestion Flow"**.

**What happens:**
*   **Ingestion**: The backend (`services/ingestion_service.py`) parses the PDF using `pypdf`.
*   **Chunking**: Text is split into meaningful chunks.
*   **Vector Storage**: Chunks are embedded and stored in the **local ChromaDB** (`local_data/vector_store`).

### B. Agentic AI Core & Content Generation
1.  Navigate to **"New Goal"** or **"Agent Debugger"**.
2.  When you input a learning goal (e.g., "Learn about Eigenvectors"):
    *   The system queries **ChromaDB** for relevant content from your uploaded PDFs.
    *   The **Agentic Core** (Tree of Thought) plans a curriculum based on this retrieved context.
    *   The output is passed to the **Content Generator** to create the final educational material.

---

## Troubleshooting

-   **Backend Crashes?** Check if port 8000 is free (`netstat -ano | findstr :8000`).
-   **"Module Not Found"?** Ensure you verify the virtual environment is active (look for `(venv)` prefix).
-   **Database Access?** The app currently connects to a default MongoDB Atlas cluster. Check `db/connection.py` if you need to change targets.
