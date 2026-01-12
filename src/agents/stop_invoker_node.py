"""
Stop Invoker Node - Bridges Shipment-level and Stop-level processing

This node:
- Operates at Shipment level
- Extracts current Stop
- Invokes stop subgraph with StopState
- Rolls up results back to Shipment level
"""
from src.agents import ShipmentState, StopState
from src.agents.stop_subgraph import stop_subgraph


def stop_invoker_node(state: ShipmentState) -> ShipmentState:
    """
    Invoke stop processing for the current stop.
    
    This demonstrates:
    - State conversion from Shipment → Stop level
    - Invoking Stop-level processing
    - Rolling up results from Stop → Shipment level
    """
    current_stop_index = state["current_stop_index"]
    shipment = state["shipment"]
    
    # Check if all stops are processed
    if current_stop_index >= len(shipment.stops):
        print("\n=== All stops processed ===")
        return {
            **state,
            "processing_complete": True
        }
    
    current_stop = shipment.stops[current_stop_index]
    
    print(f"\n=== Processing Stop {current_stop_index + 1}/{len(shipment.stops)} ===")
    
    # Create Stop-level state
    stop_state: StopState = {
        "stop": current_stop,
        "po_results": {},
        "all_pos_processed": False,
        "needs_human_review": False,
        "escalation_message": None
    }
    
    # Invoke stop subgraph (which handles PO subgraph invocation)
    stop_result = stop_subgraph.invoke(stop_state)
    
    # Update the stop in the shipment with processed version
    shipment.stops[current_stop_index] = stop_result["stop"]
    
    # Roll up results to shipment level
    stop_results = state.get("stop_results", {})
    stop_results[current_stop.id] = stop_result["po_results"]
    
    return {
        **state,
        "shipment": shipment,
        "stop_results": stop_results
    }


def check_if_complete(state: ShipmentState) -> str:
    """
    Check if all stops are processed.
    
    Returns:
        'complete': All stops done
        'continue': More stops to process
    """
    current_stop_index = state["current_stop_index"]
    shipment = state["shipment"]
    
    if state.get("processing_complete", False):
        return "complete"
    
    if current_stop_index >= len(shipment.stops):
        return "complete"
    
    return "continue"
