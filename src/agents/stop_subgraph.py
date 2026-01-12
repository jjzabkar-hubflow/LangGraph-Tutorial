"""
Stop Subgraph - Handles processing of a stop including its POs via subgraph
This creates a proper hierarchical structure for xray visualization
"""
from langgraph.graph import StateGraph, START, END
from src.agents import StopState, POState
from src.agents.model import StopType
from src.agents.po_subgraph import po_subgraph


def check_stop_type_node(state: StopState) -> StopState:
    """Check and mark the stop type."""
    stop = state["stop"]
    print(f"\n--- Processing Stop ID: {stop.id} ---")
    print(f"Stop Type: {stop.type}")
    print(f"POs in stop: {len(stop.po_list)}")
    
    # For PICK_UP stops, mark as skipped
    if stop.type == StopType.PICK_UP:
        print(f"⚠️  PICK_UP stop detected - marking as non-escalated and skipping")
        stop.is_escalated = False
        stop.escalation_reason = None
        
        return {
            **state,
            "stop": stop,
            "po_results": {},
            "all_pos_processed": True,
            "needs_human_review": False,
            "escalation_message": None
        }
    
    return state


def prepare_po_processing(state: StopState) -> StopState:
    """Prepare for PO processing."""
    stop = state["stop"]
    print(f"✓ DROP_OFF stop - preparing to process {len(stop.po_list)} POs")
    return state


def process_single_po_wrapper(state: StopState) -> StopState:
    """
    Wrapper node that processes a single PO through the subgraph.
    In a real implementation, this would be parallelized across all POs.
    For visualization purposes, this shows the PO subgraph integration.
    """
    stop = state["stop"]
    
    # Process each PO through the PO subgraph
    # Note: In production, this would be done in parallel
    po_results = {}
    any_escalated = False
    escalation_messages = []
    
    for po in stop.po_list:
        # Create PO-level state
        po_state: POState = {
            "po": po,
            "processing_result": "",
            "needs_review": False,
            "escalation_message": None
        }
        
        # Invoke PO subgraph
        po_result = po_subgraph.invoke(po_state)
        
        # Collect results
        po_results[po.po_num] = po_result["processing_result"]
        
        if po_result.get("needs_review") or po_result["processing_result"] == "ESCALATED":
            any_escalated = True
            if po_result.get("escalation_message"):
                escalation_messages.append(po_result["escalation_message"])
        
        # Update the PO in the stop with processed version
        for idx, stop_po in enumerate(stop.po_list):
            if stop_po.po_num == po.po_num:
                stop.po_list[idx] = po_result["po"]
                break
    
    # Roll up escalation to stop level if any PO was escalated
    if any_escalated:
        stop.is_escalated = True
        stop.escalation_reason = "; ".join(escalation_messages) if escalation_messages else "One or more POs escalated"
    else:
        stop.is_escalated = False
        stop.escalation_reason = None
    
    print(f"✓ All POs processed for stop {stop.id}")
    print(f"  Results: {po_results}")
    print(f"  Stop escalated: {stop.is_escalated}")
    
    return {
        **state,
        "stop": stop,
        "po_results": po_results,
        "all_pos_processed": True,
        "needs_human_review": any_escalated,
        "escalation_message": stop.escalation_reason
    }


def check_stop_type(state: StopState) -> str:
    """Routing function for stop type."""
    if state["stop"].type == StopType.PICK_UP:
        return "pickup"
    return "dropoff"


# Node names
CHECK_STOP_TYPE = "check_stop_type"
PREPARE_PO = "prepare_po_processing"
PO_PROCESSOR = "process_pos"

# Build stop processing subgraph
stop_graph_builder = StateGraph(StopState)

# Add nodes
stop_graph_builder.add_node(CHECK_STOP_TYPE, check_stop_type_node)
stop_graph_builder.add_node(PREPARE_PO, prepare_po_processing)
stop_graph_builder.add_node(PO_PROCESSOR, process_single_po_wrapper)

# Start -> Check stop type
stop_graph_builder.add_edge(START, CHECK_STOP_TYPE)

# Route based on stop type
stop_graph_builder.add_conditional_edges(
    CHECK_STOP_TYPE,
    check_stop_type,
    {
        "pickup": END,          # Skip PO processing
        "dropoff": PREPARE_PO   # Prepare for PO processing
    }
)

# After preparation, process POs
stop_graph_builder.add_edge(PREPARE_PO, PO_PROCESSOR)

# After PO processing, end
stop_graph_builder.add_edge(PO_PROCESSOR, END)

# Compile the stop subgraph
stop_subgraph = stop_graph_builder.compile()
