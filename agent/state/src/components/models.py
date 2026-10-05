"""
Core domain models and security constraints for the state module.
"""
import datetime
from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass
class BookingContext:
    """
    Central state store for an ongoing booking conversation.
    Tracks guest requirements, intermediate results, and agent trace data.
    """
    # Guest requirements
    destination: str | None = None
    check_in: datetime.date | None = None
    check_out: datetime.date | None = None
    guests: int | None = None
    guest_name: str | None = None
    guest_phone: str | None = None
    budget_per_night: float | None = None
    room_preference: str | None = None
    special_requirements: list[str] = field(default_factory=list)

    # Selected results
    selected_property_id: str | None = None
    selected_room_id: str | None = None
    add_ons: list[str] = field(default_factory=list)
    booking_hold_ref: str | None = None

    # Agent trace (for debug panel)
    last_tool_called: str | None = None
    last_tool_result: dict[str, Any] | None = None
    last_action: Literal["ask_question", "call_tool", "recommend", "hold"] | None = None
    tool_traces: list[dict[str, Any]] = field(default_factory=list)
    pending_alternatives: list[dict[str, Any]] = field(default_factory=list)
    conversation_history: list[dict[str, Any]] = field(default_factory=list)


# Explicit whitelist of fields that can be modified via partial state updates.
ALLOWED_DELTA_FIELDS = frozenset([
    "destination",
    "check_in",
    "check_out",
    "guests",
    "guest_name",
    "guest_phone",
    "budget_per_night",
    "room_preference",
    "special_requirements",
    "selected_property_id",
    "selected_room_id",
    "add_ons",
    "booking_hold_ref",
    "last_action"
])


class ProtectedFieldError(Exception):
    """Raised when an update attempts to modify a protected state field not in ALLOWED_DELTA_FIELDS."""
    pass
