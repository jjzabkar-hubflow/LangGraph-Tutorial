"""
Shipment Processing Graph Builder with Hierarchical States

This graph demonstrates:
1. Hierarchical state management (Shipment → Stop → PO)
2. Processing at appropriate levels (ShipmentState, StopState, POState)
3. Parallel PO processing via subgraphs
4. State rollup from child to parent levels
5. Deterministic processing (skipping PICK_UP stops)
6. Human-in-the-loop at PO level (within subgraph)
"""
from langgraph.graph import StateGraph, START, END

from src.agents import ShipmentState
from src.agents.shipment_processor_node import shipment_processor_node
from src.agents.stop_invoker_node import stop_invoker_node, check_if_complete
from src.agents.next_stop_node import next_stop_node

# Node names
SHIPMENT_PROCESSOR = "shipment_processor"
STOP_INVOKER = "stop_invoker"
NEXT_STOP = "next_stop"

# Build the shipment processing graph (operates at Shipment level)
graph_builder = StateGraph(ShipmentState)

# Add nodes
graph_builder.add_node(SHIPMENT_PROCESSOR, shipment_processor_node)
graph_builder.add_node(STOP_INVOKER, stop_invoker_node)
graph_builder.add_node(NEXT_STOP, next_stop_node)

# Start -> Initialize shipment processing
graph_builder.add_edge(START, SHIPMENT_PROCESSOR)

# Shipment processor -> Stop invoker
graph_builder.add_edge(SHIPMENT_PROCESSOR, STOP_INVOKER)

# After stop processing, check if complete
graph_builder.add_conditional_edges(
    STOP_INVOKER,
    check_if_complete,
    {
        "complete": END,          # All stops processed
        "continue": NEXT_STOP     # Move to next stop
    }
)

# After advancing to next stop, process it
graph_builder.add_edge(NEXT_STOP, STOP_INVOKER)

# Compile the graph
my_graph = graph_builder.compile()

# For backward compatibility (if needed)
shipment_graph = my_graph