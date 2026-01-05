import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from fastapi.middleware.cors import CORSMiddleware
import os

from agent_core.graph import create_tot_graph
from agent_core.schemas import AgentState, ThoughtNode
from services.decomposition_service import decompose_goal
from services.ingestion_service import ingest_pdf

app = FastAPI()

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    print(">>> Agentic AI Core Starting...")
    print(f">>> VectorDB Provider: Local (ChromaDB at {os.getcwd()}/local_data)")
    print(">>> Mock VectorDB has been disabled.")

class ScenarioRequest(BaseModel):
    scenario: str # "confused" | "bored"
    topic_title: Optional[str] = None
    topic_content: Optional[str] = None

class DecomposeRequest(BaseModel):
    goal: str

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    meta: Dict[str, Any]

class SavePlanRequest(BaseModel):
    plan_data: Dict[str, Any]

class CreateSessionRequest(BaseModel):
    plan_id: str
    student_id: str

# ... (keep existing code)
from services.learning_plan_service import LearningPlanService
from services.learning_session_service import LearningSessionService

@app.post("/api/learning_plan/save")
async def save_learning_plan(request: SavePlanRequest):
    try:
        service = LearningPlanService()
        plan_id = service.save_learning_plan(request.plan_data)
        return {"status": "success", "plan_id": plan_id}
    except Exception as e:
        print(f"Save Plan Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/create")
async def create_session(request: CreateSessionRequest):
    print(f"Received Create Session Request: plan_id={request.plan_id}, student_id={request.student_id}")
    try:
        service = LearningSessionService()
        session_id = service.create_session(request.plan_id, request.student_id)
        print(f"Session Created Successfully: {session_id}")
        return {"status": "success", "session_id": session_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Create Session Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    service = LearningSessionService()
    data = service.get_session_details(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Session not found")
    return data

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a learning session.
    """
    service = LearningSessionService()
    success = service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or could not be deleted")
    return {"message": "Session deleted successfully"}

@app.get("/api/sessions/student/{student_id}")
async def get_student_sessions(student_id: str):
    try:
        service = LearningSessionService()
        sessions = service.get_sessions_by_student(student_id)
        return {"sessions": sessions}
    except Exception as e:
        print(f"List Sessions Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def transform_state_to_graph(state: AgentState) -> GraphResponse:
    tree_memory = state["tree_memory"]
    best_node = state["best_node"]
    
    # Identify Best Path IDs
    best_path_ids = set()
    curr = best_node
    while curr:
        best_path_ids.add(curr.id)
        if curr.parent_id:
            curr = tree_memory.get(curr.parent_id)
        else:
            curr = None
            
    nodes = []
    edges = []
    
    # Build Nodes & Edges
    for node_id, node in tree_memory.items():
        # Determine styling class based on local score
        node_class = "node-default"
        if node.score >= 0.8:
            node_class = "node-high-score"
        elif node.score < 0.5:
            node_class = "node-low-score"
            
        # Node
        nodes.append({
            "id": node.id,
            "data": {
                "label": node.content[:50] + "..." if len(node.content) > 50 else node.content,
                "fullContent": node.content,
                "localScore": node.score,
                "pathScore": node.path_score,
                "depth": node.depth,
                "type": node.metadata.get("type", "unknown"),
                "directive": node.metadata.get("directive"), # Pass full directive to UI
                "isBestPath": node_id in best_path_ids
            },
            "type": "thoughtNode", # Custom type for React Flow
            "position": {"x": 0, "y": 0}, # Layout handles this
            "className": node_class
        })
        
        # Edge (if parent exists)
        if node.parent_id:
            edge_class = "edge-default"
            if node_id in best_path_ids and node.parent_id in best_path_ids:
                edge_class = "edge-selected"
            elif node_id not in best_path_ids:
                edge_class = "edge-pruned" # Simple heuristic: if not best, consider pruned/alternative
                
            edges.append({
                "id": f"{node.parent_id}-{node_id}",
                "source": node.parent_id,
                "target": node_id,
                "className": edge_class,
                "animated": node_id in best_path_ids
            })

    return GraphResponse(
        nodes=nodes,
        edges=edges,
        meta={
            "best_path_ids": list(best_path_ids),
            "final_response": state.get("final_response", ""),
            "run_stats": {
                "total_nodes": len(tree_memory),
                "depth": state.get("frontier", [ThoughtNode(content="", depth=0)])[0].depth if state.get("frontier") else 0
            },
            "context_data": state.get("context_data", {}), # Expose CV/RL signals to UI
            "profile": state.get("profile", {}),
            "tie_break_trace": state.get("tie_break_trace")
        }
    )

@app.post("/api/run_sim", response_model=GraphResponse)
async def run_simulation(req: ScenarioRequest):
    print(f"Running scenario: {req.scenario}")
    
    student_id = "alex_123"
    
    # Use real topic if provided, else fallback to mock default
    if req.topic_title:
        query = f"I want to learn about {req.topic_title}"
        print(f"Using Real Topic Context: {req.topic_title}")
    else:
        query = "Teach me the quadratic formula"
        
    cv_state = "neutral"
    
    if req.scenario == "confused":
        cv_state = "confused"
    elif req.scenario == "bored":
        cv_state = "bored"
        
    # Inject real content into context if available
    context_data = {"test_cv_state": cv_state}
    if req.topic_content:
        context_data["topic_content"] = req.topic_content
        
    initial_state = {
        "student_id": student_id,
        "user_query": query,
        "context_data": context_data,
        "frontier": [],
        "tree_memory": {},
        "best_node": None
    }
    
    # Run Agent
    agent = create_tot_graph()
    try:
        final_state = agent.invoke(initial_state, config={"recursion_limit": 20})
        return transform_state_to_graph(final_state)
    except Exception as e:
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/goal_decompose")
async def goal_decompose(req: DecomposeRequest):
    print(f"Decomposing goal: {req.goal}")
    try:
        result = decompose_goal(req.goal)
        return result
    except Exception as e:
        print(f"Decomposition Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Ingests a PDF file into the Local VectorDB.
    """
    print(f"Received upload: {file.filename}")
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
            
        content = await file.read()
        result = await ingest_pdf(content, file.filename)
        return result
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
