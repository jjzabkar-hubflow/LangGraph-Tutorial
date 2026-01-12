"""
NextStop node - Operates at Shipment level to advance to next stop
"""
from src.agents import ShipmentState


def next_stop_node(state: ShipmentState) -> ShipmentState:
    """
    Advance to the next stop after current stop is processed.
    This operates at the Shipment level.
    """
    current_stop_index = state["current_stop_index"]
    
    print(f"\n→ Moving to next stop (from index {current_stop_index} to {current_stop_index + 1})")
    
    return {
        **state,
        "current_stop_index": current_stop_index + 1
    }
