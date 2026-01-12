"""
Main entry point for the Shipment Processing Graph Tutorial

This demonstrates:
- Shipment processing with multiple stops
- PICK_UP vs DROP_OFF deterministic routing
- PO-level processing with escalations
- Human-in-the-loop for escalation resolution
- Partial state changes at Stop and PO levels
"""
import json
import uuid
from pathlib import Path
from dotenv import load_dotenv

from src.agents.graph_builder import my_graph
from src.agents.model import Shipment, Stop, PurchaseOrder, ShipmentStatus, StopType, PoState
from src.util.mermaid import create_mermaid_diagram_files

load_dotenv()


def create_sample_shipment() -> Shipment:
    """
    Create a sample shipment from sample_shipment.json file.
    """
    # Load the JSON file
    json_path = Path(__file__).parent / "sample_shipment.json"
    with open(json_path, "r") as f:
        data = json.load(f)
    
    # Parse PurchaseOrders for each stop
    stops = []
    for stop_data in data["stops"]:
        po_list = [
            PurchaseOrder(
                po_num=po["po_num"],
                po_state=PoState(po["po_state"]),
                is_escalated=po["is_escalated"],
                escalation_reason=po.get("escalation_reason")
            )
            for po in stop_data["po_list"]
        ]
        
        stop = Stop(
            id=stop_data["id"],
            shipment_id=stop_data["shipment_id"],
            type=StopType(stop_data["type"]),
            is_escalated=stop_data["is_escalated"],
            escalation_reason=stop_data.get("escalation_reason"),
            po_list=po_list
        )
        stops.append(stop)
    
    # Create the shipment
    shipment = Shipment(
        id=data["id"],
        tms_id=data["tms_id"],
        bol_num=data["bol_num"],
        status=ShipmentStatus(data["status"]),
        stops=stops
    )
    
    return shipment


def run_shipment_processing():
    """
    Run the shipment processing workflow.
    """
    print("\n" + "="*70)
    print("LANGGRAPH SHIPMENT PROCESSING TUTORIAL")
    print("="*70)
    
    # Create sample shipment
    shipment = create_sample_shipment()
    
    # Initialize state
    initial_state = {
        "shipment": shipment,
        "current_stop_index": 0,
        "stop_results": {},
        "processing_complete": False
    }
    
    # Run the graph
    final_state = my_graph.invoke(initial_state)
    
    # Display results
    print("\n" + "="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"\nShipment ID: {final_state['shipment'].id}")
    print(f"Processing Complete: {final_state['processing_complete']}")
    
    print(f"\nStop Processing Results:")
    for stop_id, po_results in final_state.get('stop_results', {}).items():
        print(f"  Stop {stop_id}:")
        for po_num, result in po_results.items():
            print(f"    {po_num}: {result}")
    
    print("\nStop Summary:")
    for idx, stop in enumerate(final_state['shipment'].stops):
        print(f"  Stop {idx + 1} (ID: {stop.id}):")
        print(f"    Type: {stop.type}")
        print(f"    Escalated: {stop.is_escalated}")
        print(f"    POs: {len(stop.po_list)}")
        for po in stop.po_list:
            print(f"      - {po.po_num}: {po.po_state.value} (Escalated: {po.is_escalated})")


if __name__ == "__main__":
    # Generate mermaid diagram
    create_mermaid_diagram_files()
    print('✓ Updated mermaid diagram\n')
    
    # Run shipment processing
    run_shipment_processing()
