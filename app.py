"""
Flask API for Shipment Processing Graph

This demonstrates:
- REST API endpoint for shipment processing
- Streaming shipment processing status updates
- JSON-based shipment submission
"""
from flask import Flask, Response, request, stream_with_context, jsonify
import json
import uuid
from src.agents.graph_builder import my_graph
from src.agents.model import Shipment, Stop, PurchaseOrder, ShipmentStatus, StopType, PoState
from src.util.mermaid import create_mermaid_diagram_files
from pydantic import ValidationError

print('creating flask app')
app = Flask(__name__)
print('created flask app')
create_mermaid_diagram_files()
print('updated mermaid diagram')


@app.route('/process-shipment', methods=['POST'])
def process_shipment():
    """
    Process a shipment through the LangGraph workflow.
    
    Expects JSON payload with shipment data:
    {
        "id": 1001,
        "tms_id": "TMS-2026-001",
        "bol_num": "BOL-ABC123",
        "status": "NEW",
        "stops": [...]
    }
    """
    data = request.get_json()
    if not data:
        return {"error": "Invalid input. Shipment data required."}, 400
    
    try:
        # Parse shipment from JSON
        shipment = Shipment(**data)
        
        # Initialize state
        initial_state = {
            "shipment": shipment,
            "current_stop_index": 0,
            "stop_results": {},
            "processing_complete": False
        }
        
        # Process shipment
        final_state = my_graph.invoke(initial_state)
        
        # Return results
        return jsonify({
            "success": True,
            "shipment_id": final_state['shipment'].id,
            "processing_complete": final_state['processing_complete'],
            "stop_results": final_state.get('stop_results', {}),
            "stops_processed": len(final_state['shipment'].stops)
        })
        
    except ValidationError as e:
        return {"error": f"Invalid shipment data: {str(e)}"}, 400
    except Exception as e:
        return {"error": f"Processing error: {str(e)}"}, 500


@app.route('/stream-shipment', methods=['POST'])
def stream_shipment():
    """
    Stream shipment processing updates in real-time.
    """
    data = request.get_json()
    if not data:
        return {"error": "Invalid input. Shipment data required."}, 400
    
    try:
        shipment = Shipment(**data)
        
        initial_state = {
            "shipment": shipment,
            "current_stop_index": 0,
            "stop_results": {},
            "processing_complete": False
        }
        
        def generate_stream():
            """Stream processing updates."""
            try:
                for chunk in my_graph.stream(initial_state, stream_mode="updates"):
                    result = json.dumps({"update": str(chunk)}) + '\n'
                    yield result
            except Exception as exc:
                yield json.dumps({"error": str(exc)}) + '\n'
        
        return Response(
            stream_with_context(generate_stream()),
            content_type='text/event-stream'
        )
        
    except ValidationError as e:
        return {"error": f"Invalid shipment data: {str(e)}"}, 400


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "shipment-processor"})


if __name__ == "__main__":
    print('Start Flask server')
    app.run(host="0.0.0.0", port=5001, debug=True)
