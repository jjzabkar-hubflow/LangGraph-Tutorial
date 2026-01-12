"""
POProcessor node - Processes individual purchase orders
This demonstrates parallel processing capabilities at the PO level
"""
from src.agents import POState
from src.agents.model import PoState as PoStateEnum
import time
import random


def po_processor_node(state: POState) -> POState:
    """
    Process a single PO at the PO level.
    
    This node demonstrates:
    - PO-level processing (operates on POState, not ShipmentState)
    - Can be invoked in parallel for multiple POs
    - Returns PO-specific results that roll up to parent Stop
    """
    po = state["po"]
    
    print(f"\n  → Processing PO: {po.po_num}")
    print(f"    State: {po.po_state}")
    print(f"    Escalated: {po.is_escalated}")
    
    # Simulate processing time
    time.sleep(random.uniform(1.0, 5.0))
    
    # Check PO state and handle escalations
    if po.po_state == PoStateEnum.ESCALATED:
        print(f"    ⚠️  PO {po.po_num} is ESCALATED")
        po.is_escalated = True
        
        if not po.escalation_reason:
            po.escalation_reason = "PO requires manual review"
        
        return {
            **state,
            "po": po,
            "processing_result": "ESCALATED",
            "needs_review": True,
            "escalation_message": f"PO {po.po_num}: {po.escalation_reason}"
        }
    
    elif po.po_state == PoStateEnum.PENDING:
        print(f"    ⏳ PO {po.po_num} is PENDING - awaiting confirmation")
        po.is_escalated = False
        
        return {
            **state,
            "po": po,
            "processing_result": "PENDING",
            "needs_review": False,
            "escalation_message": None
        }
    
    else:  # SCHEDULED
        print(f"    ✓ PO {po.po_num} is SCHEDULED - processing complete")
        po.is_escalated = False
        po.escalation_reason = None
        
        return {
            **state,
            "po": po,
            "processing_result": "SCHEDULED",
            "needs_review": False,
            "escalation_message": None
        }


def check_po_needs_review(state: POState) -> str:
    """
    Check if PO needs human review.
    
    Returns:
        'needs_review': PO is escalated
        'complete': PO processing done
    """
    if state.get("needs_review", False):
        return "needs_review"
    return "complete"


def resolve_po_escalation(state: POState) -> POState:
    """
    Resolve PO escalation after human review.
    """
    po = state["po"]
    
    print(f"  ✓ Resolving escalation for PO {po.po_num}")
    
    # Change state from ESCALATED to SCHEDULED
    if po.po_state == PoStateEnum.ESCALATED:
        po.po_state = PoStateEnum.SCHEDULED
    
    po.is_escalated = False
    po.escalation_reason = None
    
    return {
        **state,
        "po": po,
        "processing_result": "SCHEDULED",
        "needs_review": False,
        "escalation_message": None
    }
