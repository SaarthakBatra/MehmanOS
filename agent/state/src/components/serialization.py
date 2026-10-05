"""
Serialization and deserialization logic for BookingContext.
"""
import datetime
from dataclasses import asdict
from typing import Any

from agent.state.src.components.models import BookingContext
from agent.state.src.components.coercion import _coerce_value


def _serialize_obj(obj: Any) -> Any:
    """
    Recursively serializes complex objects (dicts, lists, dataclasses, pydantic models) 
    into JSON-serializable basic types.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Any: A JSON-serializable representation of the object.
    """
    if isinstance(obj, dict):
        return {k: _serialize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize_obj(i) for i in obj]
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json', exclude_none=True)
    if hasattr(obj, '__dict__'):
        return {k: _serialize_obj(v) for k, v in obj.__dict__.items()}
    return obj


def context_to_dict(context: BookingContext) -> dict:
    """
    Converts a BookingContext instance into a plain dictionary suitable for JSON serialization.
    Dates are converted to ISO 8601 strings.

    Args:
        context (BookingContext): The context to serialize.

    Returns:
        dict: The serialized context data.
    """
    d = asdict(context)
    for k, v in d.items():
        if isinstance(v, datetime.date):
            d[k] = v.isoformat()
        elif k in ("conversation_history", "tool_traces") and v:
            # Recursively serialize complex nested structures (e.g. tool arguments)
            d[k] = _serialize_obj(v)
    return d


def dict_to_context(data: dict) -> BookingContext:
    """
    Creates a new BookingContext instance from a raw dictionary of data.
    Fields are coerced to their expected types. Deserialization failures result in
    the field being set to None and an error being logged.

    Args:
        data (dict): The raw dictionary data to deserialize.

    Returns:
        BookingContext: A populated BookingContext instance.
    """
    context = BookingContext()
    for key, value in data.items():
        if hasattr(context, key):
            try:
                coerced_val = _coerce_value(key, value)
                setattr(context, key, coerced_val)
            except ValueError as e:
                # Set field to None on deserialization failure
                setattr(context, key, None)
                import agent.state.src.state
                agent.state.src.state.log_error(
                    payload={"field": key, "invalid_value": value, "reason": str(e)},
                    event_type="ERR_STATE_DESERIALIZATION_FAILED"
                )
    return context
