"""
PO Subgraph - Handles parallel processing of individual Purchase Orders

This subgraph:
- Operates at the PO level (POState)
- Can process multiple POs in parallel
- Handles PO-level escalations with human review
- Returns results that roll up to parent Stop
"""
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents import POState
from src.agents.po_processor_node import (
    po_processor_node,
    check_po_needs_review,
    resolve_po_escalation
)

# Node names
PO_PROCESSOR = "po_processor"
PO_REVIEW = "po_review"

# Build PO processing subgraph
po_graph_builder = StateGraph(POState)

# Add nodes
po_graph_builder.add_node(PO_PROCESSOR, po_processor_node)
po_graph_builder.add_node(PO_REVIEW, resolve_po_escalation)

# Start -> Process PO
po_graph_builder.add_edge(START, PO_PROCESSOR)

# After processing, check if review needed
po_graph_builder.add_conditional_edges(
    PO_PROCESSOR,
    check_po_needs_review,
    {
        "needs_review": PO_REVIEW,  # Escalated - resolve it
        "complete": END              # Processing done
    }
)

# After review, check if resolved or needs to loop back
po_graph_builder.add_conditional_edges(
    PO_REVIEW,
    check_po_needs_review,
    {
        "needs_review": PO_REVIEW,  # Still needs review - loop again
        "complete": END              # Resolved - done
    }
)

# Compile the PO subgraph with checkpointer for parallel execution support
# The checkpointer enables state persistence and parallel execution coordination
po_subgraph = po_graph_builder.compile(checkpointer=MemorySaver())
