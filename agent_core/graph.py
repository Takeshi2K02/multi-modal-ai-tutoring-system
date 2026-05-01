from langgraph.graph import StateGraph, END
from agent_core.schemas import AgentState
from agent_core.nodes.context_node import retrieve_context
from agent_core.nodes.expand_node import expand_frontier
from agent_core.nodes.evaluate_node import evaluate_frontier
from agent_core.nodes.prune_node import prune_frontier, check_stop_condition
from agent_core.nodes.finalize_node import finalize_output, background_synthesis

def create_tot_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("expand_frontier", expand_frontier)
    workflow.add_node("evaluate_frontier", evaluate_frontier)
    workflow.add_node("prune_frontier", prune_frontier)
    workflow.add_node("background_synthesis", background_synthesis)
    workflow.add_node("finalize_output", finalize_output)
    
    workflow.set_entry_point("retrieve_context")
    
    workflow.add_edge("retrieve_context", "expand_frontier")
    workflow.add_edge("expand_frontier", "evaluate_frontier")
    workflow.add_edge("evaluate_frontier", "prune_frontier")
    
    workflow.add_conditional_edges(
        "prune_frontier",
        check_stop_condition,
        {
            "expand": "expand_frontier",
            "finalize": "finalize_output",
            "shadow": "background_synthesis"
        }
    )
    
    workflow.add_edge("background_synthesis", END)
    workflow.add_edge("finalize_output", END)
    
    return workflow.compile()