"""
POProcessor node - Processes individual purchase orders
This demonstrates parallel processing capabilities at the PO level
"""
from src.agents import POState
from src.agents.model import PoState as PoStateEnum
from src.chat.service.llm_chat_model_service import llm
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
    
    print(f"\n  → Processing PO: {po.po_num}, State: {po.po_state}, Escalated: {po.is_escalated}")
    
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
    Resolve PO escalation by requesting human input via LLM.
    If input is acceptable, resolve the state.
    Otherwise, keep needs_review=True to loop again.
    """
    po = state["po"]
    
    print(f"\n  🤖 Requesting human input for escalated PO {po.po_num}")
    print(f"     Escalation reason: {po.escalation_reason}")
    raw_input = input(f"  📫Enter your input (simulating email resolution): ")
    
    # Use LLM to ask for human input
    prompt = f"""Evaluate the following input to determine if the PO should be approved or rejected.

Purchase Order: {po.po_num}
Purchase Order State: {po.po_state}
Purchase Order Escalated: {po.is_escalated}
Purchase Order Escalation Reason: {po.escalation_reason}

Input: {raw_input}

Possible states to return:
    SCHEDULED: if approved, looks good, or otherise schedule
    PENDING: if still in progress, or otherwise incomplete
    ESCALATED: if there is still a problem. Update the escalation reason and return the escalated state.

What is your decision?"""
    
    # Get human input via LLM
    response = llm.invoke([{"role": "user", "content": prompt}])
    human_input = response.content.strip().lower()
    
    print(f"     Human input received: {human_input}")
    
    # Check if input is acceptable (approve keywords)
    approve_keywords = ["approve", "accept", "schedule", "looks good", "ok", "yes", "proceed", "continue"]
    is_acceptable = any(keyword in human_input for keyword in approve_keywords)
    
    if is_acceptable:
        print(f"  ✓ Input accepted - Resolving escalation for PO {po.po_num}")
        
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
    else:
        print(f"  ⚠️  Input not acceptable - PO {po.po_num} requires additional review")
        
        # Keep escalated state and loop again
        return {
            **state,
            "po": po,
            "processing_result": "ESCALATED",
            "needs_review": True,
            "escalation_message": f"PO {po.po_num} requires additional review. Human input: {human_input}"
        }
