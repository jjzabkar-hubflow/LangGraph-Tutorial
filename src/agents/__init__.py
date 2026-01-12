from typing import Annotated, Literal
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from src.agents.model import Shipment, Stop, PurchaseOrder


class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None

class MessageClassifier(BaseModel):
    message_type: Literal[
        "emotional",
        "logical",
        "music"
    ] = Field(
        ...,
        description="Classify if the message requires a musical, emotional (therapist), or logical response."
    )

# Hierarchical state for shipment processing workflow

class POState(TypedDict):
    """State for individual PO processing (lowest level)"""
    po: PurchaseOrder
    processing_result: str  # SCHEDULED, PENDING, ESCALATED
    needs_review: bool
    escalation_message: str | None

class StopState(TypedDict):
    """State for stop processing (middle level)"""
    stop: Stop
    po_results: dict[str, str]  # Maps PO number to processing result
    all_pos_processed: bool
    needs_human_review: bool
    escalation_message: str | None

class ShipmentState(TypedDict):
    """State for shipment processing (top level)"""
    shipment: Shipment
    current_stop_index: int
    stop_results: dict[int, dict[str, str]]  # Maps stop ID to its PO results
    processing_complete: bool
