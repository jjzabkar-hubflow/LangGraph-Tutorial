from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class ShipmentStatus(Enum):
    NEW = "NEW"
    ESCALATED = "ESCALATED"
    NEEDS_ACTION = "NEEDS_ACTION"
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"

class StopType(str, Enum):
    PICK_UP = "PICK_UP"
    DROP_OFF = "DROP_OFF"

class PoState(str, Enum):
    """ 
    SCHEDULED: The PO is scheduled for pickup or delivery.
    PENDING: The PO is pending approval (for example, if the PO is awaiting scheduling confirmation).
    ESCALATED: The PO is escalated and requires action.
    """
    SCHEDULED = "SCHEDULED"
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"

class PurchaseOrder(BaseModel):
    po_num: str
    po_state: PoState
    is_escalated: bool 
    escalation_reason: str | None = Field(
        default=None,
        description="Escalation reason for the PO",
    )

class Stop(BaseModel):
    """
    A stop is a location where a shipment is picked up or dropped off.
    A stop can contain zero to many purchase orders.
    Note that this model differs from the model in the hubflow-api code base
    so that we can show PO hierarchy processing capabilities.
    """
    id: int
    shipment_id: int
    # po_num: list[str] = Field(default_factory=list)
    po_list: list[PurchaseOrder] = Field(default_factory=list)
    is_escalated: bool 
    type: StopType 
    escalation_reason: str | None = Field(
        default=None,
        description="Escalation reason for the stop",
    )

class Shipment(BaseModel):
    id: int
    tms_id: str
    bol_num: str 
    status: ShipmentStatus
    stops: list[Stop] = Field(default_factory=list)
