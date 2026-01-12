"""
Main entry point for the Shipment Processing Graph Tutorial

This demonstrates:
- Shipment processing with multiple stops
- PICK_UP vs DROP_OFF deterministic routing
- PO-level processing with escalations
- Human-in-the-loop for escalation resolution
- Partial state changes at Stop and PO levels
"""
import uuid
from dotenv import load_dotenv

from src.agents.graph_builder import my_graph
from src.agents.model import Shipment, Stop, PurchaseOrder, ShipmentStatus, StopType, PoState
from src.util.mermaid import create_mermaid_diagram_files

load_dotenv()


def create_sample_shipment() -> Shipment:
    """
    Create a sample shipment for demonstration purposes.
    """
    shipment = Shipment(
        id=1001,
        tms_id="TMS-2026-001",
        bol_num="BOL-ABC123",
        status=ShipmentStatus.NEW,
        stops=[]
    )
    
    # Stop 1: PICK_UP (should be skipped)
    stop1 = Stop(
        id=1,
        shipment_id=shipment.id,
        type=StopType.PICK_UP,
        is_escalated=False,
        po_list=[
            PurchaseOrder(
                po_num="PO-001",
                po_state=PoState.SCHEDULED,
                is_escalated=False
            )
        ]
    )
    
    # Stop 2: DROP_OFF with mixed PO states
    stop2 = Stop(
        id=2,
        shipment_id=shipment.id,
        type=StopType.DROP_OFF,
        is_escalated=False,
        po_list=[
            PurchaseOrder(
                po_num="PO-002",
                po_state=PoState.SCHEDULED,
                is_escalated=False
            ),
            PurchaseOrder(
                po_num="PO-003",
                po_state=PoState.PENDING,
                is_escalated=False
            ),
            PurchaseOrder(
                po_num="PO-004",
                po_state=PoState.ESCALATED,
                is_escalated=True,
                escalation_reason="Delivery location requires special access"
            )
        ]
    )
    
    # Stop 3: DROP_OFF with all scheduled POs
    stop3 = Stop(
        id=3,
        shipment_id=shipment.id,
        type=StopType.DROP_OFF,
        is_escalated=False,
        po_list=[
            PurchaseOrder(
                po_num="PO-005",
                po_state=PoState.SCHEDULED,
                is_escalated=False
            ),
            PurchaseOrder(
                po_num="PO-006",
                po_state=PoState.SCHEDULED,
                is_escalated=False
            )
        ]
    )
    
    shipment.stops = [stop1, stop2, stop3]
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
