# LangGraph Shipment Processing Tutorial

A comprehensive LangGraph tutorial demonstrating advanced workflow patterns for shipment processing with stops and purchase orders.

Original Tutorial: https://www.youtube.com/watch?v=aywZrzNaKjs

Forked base: https://github.com/techwithtim/LangGraph-Tutorial

![Mermaid diagram](./src/util/mermaid.png)

## Overview

This tutorial demonstrates a real-world shipment processing workflow that showcases:

### 1. **Hierarchical Processing**
   - Process a `Shipment` containing multiple `Stops`
   - Each `Stop` contains multiple `PurchaseOrders` (POs)
   - Demonstrates nested iteration through complex data structures

### 2. **Deterministic Routing with Conditional Nodes**
   - PICK_UP stops are automatically skipped (marked as non-escalated)
   - DROP_OFF stops are processed with full PO validation
   - Conditional edges determine processing flow based on stop type

### 3. **Partial State Changes**
   - Stop-level escalation status updates (`is_escalated`, `escalation_reason`)
   - PO-level state changes propagate to parent Stop
   - Demonstrates fine-grained state management

### 4. **Human-in-the-Loop Pattern**
   - Escalations trigger workflow interruption
   - Human review node simulates manual intervention
   - Resume processing after escalation resolution
   - Perfect for approval workflows and exception handling

### 5. **Parallel Processing with State Rollup** ⚡ NEW!
   - **PO-level processing**: Each PO processed through isolated subgraph
   - **True parallel execution**: Multiple POs processed concurrently using ThreadPoolExecutor
   - **Thread-safe state**: MemorySaver checkpointer with unique thread_ids
   - **Performance**: ~3x faster processing with typical PO counts
   - **State rollup**: Results roll up from PO → Stop → Shipment levels
   - **Subgraph invocation**: Stop processor invokes PO subgraph in parallel
   - 📖 **See**: `PARALLEL_PROCESSING_QUICKSTART.md` for details

### 6. **Real-World Business Logic**
   - PO states: SCHEDULED, PENDING, ESCALATED
   - Automatic escalation detection and handling
   - Comprehensive processing result tracking

## Architecture

### Hierarchical State Management

This tutorial uses **proper state separation** at each processing level:

- **ShipmentState**: Top level - manages stop iteration
- **StopState**: Middle level - manages PO processing
- **POState**: Bottom level - individual PO processing

### Graph Flow

```
Main Graph (Shipment Level)
START → ShipmentProcessor → StopInvoker → [Complete?] → END
                                 ↓              ↓
                            [invokes]      NextStop
                                 ↓              ↓
Stop Level Processing ──────────┘              │
  ↓                                             │
  For each PO: invoke PO Subgraph              │
  Roll up results to Stop                      │
                                                │
PO Subgraph (PO Level) ←───────────────────────┘
START → POProcessor → [Escalated?] → POReview → END
```

See [HIERARCHICAL_STATE_ARCHITECTURE.md](HIERARCHICAL_STATE_ARCHITECTURE.md) for detailed architecture documentation.

## Setup

### UV Package Manager

Install [UV](https://docs.astral.sh/uv/)

```bash
brew install uv;
```

### Dependencies

```bash
uv add \
  python-dotenv \
  langgraph \
  pydantic \
  sqlmodel \
  flask ;
```

## Running the Tutorial

### Command Line Demo

```bash
uv run main.py
```

This will:
- Create a sample shipment with 3 stops (1 PICK_UP, 2 DROP_OFF)
- Process POs with mixed states (SCHEDULED, PENDING, ESCALATED)
- Demonstrate human-in-the-loop for escalations
- Show partial state updates at Stop and PO levels
- Generate a mermaid diagram of the workflow

### Flask API Server

```bash
uv run app.py
```

API Endpoints:
- `POST /process-shipment` - Submit shipment for processing
- `POST /stream-shipment` - Stream processing updates
- `GET /health` - Health check

Example request:
```bash
curl -X POST http://localhost:5001/process-shipment \
  -H "Content-Type: application/json" \
  -d @sample_shipment.json
```

## Key Concepts Demonstrated

### 1. Conditional Routing
The `should_skip_stop()` function demonstrates deterministic routing:
- Returns `"skip"` for PICK_UP stops
- Returns `"process_pos"` for DROP_OFF stops
- Returns `"complete"` when all stops processed

### 2. State Management
`ShipmentState` tracks:
- Current stop and PO indices
- Processing results for each PO
- Escalation status and messages
- Overall processing completion

### 3. Human-in-the-Loop
`human_review_node` demonstrates:
- Workflow interruption on escalation
- Manual review simulation
- Escalation resolution
- Resume processing flow

### 4. Terminal State Aggregation
`aggregate_po_results()` shows:
- Collecting results from parallel PO processing
- Determining next action based on aggregate state
- Handling mixed success/failure scenarios

## File Structure

```
src/agents/
  ├── __init__.py                 # POState, StopState, ShipmentState
  ├── model.py                    # Data models (Shipment, Stop, PO)
  │
  ├── graph_builder.py            # Main graph (Shipment level)
  ├── shipment_processor_node.py  # Initialize (Shipment level)
  ├── stop_invoker_node.py        # Bridge Shipment→Stop, rollup results
  ├── next_stop_node.py           # Advance stop (Shipment level)
  │
  ├── po_subgraph.py              # PO subgraph definition
  ├── stop_processor_node.py      # Stop processing + PO invocation
  └── po_processor_node.py        # PO processing (PO level)
```

## Learning Path

1. **Start with `main.py`** - See the workflow in action
2. **Review `model.py`** - Understand the data structures
3. **Examine `graph_builder.py`** - See how nodes connect
4. **Study individual nodes** - Learn processing logic
5. **Experiment** - Modify stop types, PO states, escalations

## Parallel Processing Documentation ⚡

📚 **Quick Start**: `PARALLEL_PROCESSING_QUICKSTART.md` - Get started in 5 minutes  
📖 **Full Guide**: `PARALLEL_PROCESSING.md` - Comprehensive documentation  
📊 **Diagrams**: `PARALLEL_PROCESSING_DIAGRAM.md` - Visual architecture  
📝 **Changes**: `CHANGES_SUMMARY.md` - What changed and why  
🧪 **Demo**: Run `uv run python test_parallel_po.py` to see it in action

## Original Features (Preserved)

The original tutorial components are preserved in the repository history:
- Multi-agent chat system (therapist, logical, music agents)
- Message classification and routing
- LLM integration with Gemini/Ollama