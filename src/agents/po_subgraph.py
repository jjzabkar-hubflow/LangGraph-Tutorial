"""
PO Subgraph - Handles parallel processing of individual Purchase Orders

This subgraph:
- Operates at the PO level (POState)
- Can process multiple POs in parallel
- Handles PO-level escalations with human review
- Returns results that roll up to parent Stop
"""
from langgraph.graph import StateGraph, START, END
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

# After review, end
po_graph_builder.add_edge(PO_REVIEW, END)

# Compile the PO subgraph
po_subgraph = po_graph_builder.compile()
