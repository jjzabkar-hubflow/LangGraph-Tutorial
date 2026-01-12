"""
Stop Subgraph - Handles processing of a stop including its POs via subgraph
This creates a proper hierarchical structure for xray visualization
"""
from langgraph.graph import StateGraph, START, END
from src.agents import StopState, POState
from src.agents.model import StopType
from src.agents.po_subgraph import po_subgraph, po_graph_builder
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid


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


def po_subgraph_adapter(state: StopState) -> StopState:
    """
    Adapter node that processes the first PO through the subgraph.
    This node exists primarily for xray visualization - it makes the PO subgraph
    structure visible in the diagram. The actual parallel processing happens
    in the next node.
    """
    stop = state["stop"]
    
    if not stop.po_list:
        return state
    
    # Process just the first PO to demonstrate the subgraph structure
    # (The rest will be processed in parallel in the next node)
    first_po = stop.po_list[0]
    po_state: POState = {
        "po": first_po,
        "processing_result": "",
        "needs_review": False,
        "escalation_message": None
    }
    
    # This invocation makes the subgraph visible to xray
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    po_result = po_subgraph.invoke(po_state, config=config)
    
    # Update the first PO with the result
    stop.po_list[0] = po_result["po"]
    
    # Store the result for the first PO
    initial_results = {first_po.po_num: po_result["processing_result"]}
    
    return {
        **state,
        "stop": stop,
        "po_results": initial_results
    }


def process_single_po(po, stop_id: int):
    """
    Process a single PO through the subgraph in parallel.
    Returns tuple of (po_num, po_result, processed_po)
    """
    # Create PO-level state
    po_state: POState = {
        "po": po,
        "processing_result": "",
        "needs_review": False,
        "escalation_message": None
    }
    
    # Generate unique thread_id for parallel execution
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Invoke PO subgraph with config for parallel execution
    po_result = po_subgraph.invoke(po_state, config=config)
    
    return (po.po_num, po_result, po_result["po"])


def process_remaining_pos_parallel(state: StopState) -> StopState:
    """
    Process remaining POs (after the first one) in parallel.
    The first PO was already processed in the adapter node for visualization.
    """
    stop = state["stop"]
    existing_results = state.get("po_results", {})
    
    # Skip if only one PO (already processed) or no POs
    if len(stop.po_list) <= 1:
        print(f"✓ Single PO already processed for stop {stop.id}")
        return {
            **state,
            "all_pos_processed": True,
            "needs_human_review": stop.is_escalated if hasattr(stop, 'is_escalated') else False,
            "escalation_message": stop.escalation_reason if hasattr(stop, 'escalation_reason') else None
        }
    
    # Process remaining POs (skip the first one which was already processed)
    remaining_pos = stop.po_list[1:]
    print(f"⚡ Starting parallel processing of {len(remaining_pos)} remaining POs on stop {stop.id}")
    
    po_results = dict(existing_results)  # Start with existing results
    any_escalated = False
    escalation_messages = []
    processed_pos = {}
    
    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=min(len(remaining_pos), 2)) as executor:
        # Submit remaining PO processing tasks
        future_to_po = {
            executor.submit(process_single_po, po, stop.id): po 
            for po in remaining_pos
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_po):
            po_num, po_result, processed_po = future.result()
            print(f'🎯Finished processing PO {po_num}')
            
            # Collect results
            po_results[po_num] = po_result["processing_result"]
            processed_pos[po_num] = processed_po
            
            if po_result.get("needs_review") or po_result["processing_result"] == "ESCALATED":
                any_escalated = True
                if po_result.get("escalation_message"):
                    escalation_messages.append(po_result["escalation_message"])
    
    # Update remaining POs in the stop with processed versions
    for idx in range(1, len(stop.po_list)):
        po = stop.po_list[idx]
        if po.po_num in processed_pos:
            stop.po_list[idx] = processed_pos[po.po_num]
    
    # Check if first PO was also escalated
    if stop.is_escalated:
        any_escalated = True
    
    # Roll up escalation to stop level if any PO was escalated
    if any_escalated:
        stop.is_escalated = True
        if escalation_messages:
            existing_reason = stop.escalation_reason or ""
            all_messages = [existing_reason] + escalation_messages if existing_reason else escalation_messages
            stop.escalation_reason = "; ".join(all_messages)
        elif not stop.escalation_reason:
            stop.escalation_reason = "One or more POs escalated"
    else:
        stop.is_escalated = False
        stop.escalation_reason = None
    
    print(f"✓ All {len(stop.po_list)} POs processed (1 sequential + {len(remaining_pos)} parallel) for stop {stop.id}")
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
PO_SUBGRAPH_REF = "po_subgraph"  # Reference node for visualization
PO_PROCESSOR = "process_pos_parallel"

# Build stop processing subgraph
stop_graph_builder = StateGraph(StopState)

# Add nodes
stop_graph_builder.add_node(CHECK_STOP_TYPE, check_stop_type_node)
stop_graph_builder.add_node(PREPARE_PO, prepare_po_processing)

# Add PO subgraph adapter - this makes the PO subgraph visible in xray visualization
# It processes the first PO through the actual subgraph, making the structure visible
stop_graph_builder.add_node(PO_SUBGRAPH_REF, po_subgraph_adapter)

# Add the parallel processor node for remaining POs
stop_graph_builder.add_node(PO_PROCESSOR, process_remaining_pos_parallel)

# Start -> Check stop type
stop_graph_builder.add_edge(START, CHECK_STOP_TYPE)

# Route based on stop type
stop_graph_builder.add_conditional_edges(
    CHECK_STOP_TYPE,
    check_stop_type,
    {
        "pickup": END,              # Skip PO processing
        "dropoff": PREPARE_PO       # Prepare for PO processing
    }
)

# After preparation, reference the PO subgraph (for xray visualization)
stop_graph_builder.add_edge(PREPARE_PO, PO_SUBGRAPH_REF)

# From PO subgraph reference to parallel processor
# The PO_SUBGRAPH_REF node will execute once (processing first PO if any)
# then PO_PROCESSOR handles the rest in parallel
stop_graph_builder.add_edge(PO_SUBGRAPH_REF, PO_PROCESSOR)

# After parallel processing, end
stop_graph_builder.add_edge(PO_PROCESSOR, END)

# Compile the stop subgraph
stop_subgraph = stop_graph_builder.compile()
