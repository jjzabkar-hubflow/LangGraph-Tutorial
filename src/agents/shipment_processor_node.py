"""
ShipmentProcessor node - Initializes shipment processing workflow
"""
from src.agents import ShipmentState


def shipment_processor_node(state: ShipmentState) -> ShipmentState:
    """
    Initialize shipment processing at the Shipment level.
    Sets up the initial state for iterating through stops.
    """
    print(f"\n=== Starting Shipment Processing ===")
    print(f"Shipment ID: {state['shipment'].id}")
    print(f"TMS ID: {state['shipment'].tms_id}")
    print(f"BOL Number: {state['shipment'].bol_num}")
    print(f"Total Stops: {len(state['shipment'].stops)}")
    
    return {
        **state,
        "current_stop_index": 0,
        "stop_results": {},
        "processing_complete": False
    }
