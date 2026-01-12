"""
StopProcessor node - Processes individual stops in a shipment
Operates at the Stop level and invokes PO subgraph for parallel processing
"""
from src.agents import StopState, POState
from src.agents.model import StopType
from src.agents.po_subgraph import po_subgraph


def stop_processor_node(state: StopState) -> StopState:
    """
    Process a stop at the Stop level.
    
    This node demonstrates:
    - Stop-level processing (operates on StopState, not ShipmentState)
    - Invokes PO subgraph for parallel PO processing
    - Aggregates PO results and rolls them up to Stop level
    - Deterministic processing (skips PICK_UP stops)
    """
    stop = state["stop"]
    
    print(f"\n--- Processing Stop ID: {stop.id} ---")
    print(f"Stop Type: {stop.type}")
    print(f"POs in stop: {len(stop.po_list)}")
    
    # Deterministic processing: PICK_UP stops are skipped
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
    
    # For DROP_OFF stops, process POs using subgraph
    print(f"✓ DROP_OFF stop - processing POs in parallel")
    
    po_results = {}
    any_escalated = False
    escalation_messages = []
    
    # Process each PO through the PO subgraph (can be parallelized)
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
    """
    Check stop type for conditional routing.
    
    Returns:
        'pickup': PICK_UP stop (skip)
        'dropoff': DROP_OFF stop (process)
    """
    stop = state["stop"]
    
    if stop.type == StopType.PICK_UP:
        return "pickup"
    return "dropoff"
