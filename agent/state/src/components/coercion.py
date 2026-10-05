"""
Type coercion logic for booking context updates.
"""
import datetime
from typing import Any


def _coerce_value(field_name: str, value: Any) -> Any:
    """
    Coerces a raw input value to the expected type for a given BookingContext field.

    Args:
        field_name (str): The name of the field being updated.
        value (Any): The raw input value.

    Returns:
        Any: The coerced value matching the field's expected type.

    Raises:
        ValueError: If the value cannot be coerced to the expected type.
    """
    if value is None:
        # Default mutable collection fields to empty lists instead of None
        if field_name in ("special_requirements", "add_ons", "pending_alternatives", "conversation_history", "tool_traces"):
            return []
        return None
        
    if field_name in ("check_in", "check_out"):
        if type(value) is datetime.date:        # strict: rejects datetime.datetime subclass
            return value
        if isinstance(value, datetime.datetime): # explicit subclass path — strip time
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {e}")
        raise ValueError(f"Expected date string, got {type(value)}")
        
    if field_name == "guests":
        try:
            return int(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot coerce to int: {e}")
            
    if field_name == "budget_per_night":
        try:
            return float(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot coerce to float: {e}")
            
    if field_name in (
        "destination", "room_preference", "selected_property_id", 
        "selected_room_id", "booking_hold_ref", "last_tool_called", "last_action",
        "guest_name", "guest_phone"
    ):
        if isinstance(value, (str, int, float)):
            return str(value)
        raise ValueError(f"Cannot coerce {type(value)} to string")
        
    if field_name in ("special_requirements", "add_ons"):
        if not isinstance(value, list):
            raise ValueError(f"Expected list, got {type(value)}")
        
        # Coerce individual items within string lists to ensure uniformity
        coerced_list = []
        for item in value:
            if isinstance(item, (str, int, float)):
                coerced_list.append(str(item))
            else:
                raise ValueError(f"List item of type {type(item)} cannot be coerced to string")
        return coerced_list
        
    if field_name in ("pending_alternatives", "conversation_history", "tool_traces"):
        if not isinstance(value, list):
            raise ValueError(f"Expected list, got {type(value)}")
        return list(value) # shallow copy
        
    if field_name == "last_tool_result":
        if not isinstance(value, dict):
            raise ValueError(f"Expected dict, got {type(value)}")
        
        # Enforce shallow copy to prevent external mutation of state
        return dict(value)

    return value
