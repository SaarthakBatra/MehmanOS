"""
Router module for the state management system.
Exposes state logic and models via a unified interface.
"""
from typing import Any

from agent.logger.src.logger import log_error
from agent.state.src.components.models import BookingContext, ALLOWED_DELTA_FIELDS, ProtectedFieldError
from agent.state.src.components.coercion import _coerce_value as _coerce_value_internal
from agent.state.src.components.update import update_context as update_context_internal
from agent.state.src.components.serialization import (
    _serialize_obj as _serialize_obj_internal,
    context_to_dict as context_to_dict_internal,
    dict_to_context as dict_to_context_internal
)


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
def _coerce_value(field_name: str, value: Any) -> Any:
    return _coerce_value_internal(field_name, value)


"""
    Updates a BookingContext instance in-place with new values from a delta dictionary.

    Only fields listed in ALLOWED_DELTA_FIELDS can be updated. Input values are coerced
    to their appropriate types. If coercion fails, an error is logged and the field is skipped.

    Args:
        context (BookingContext): The context to update.
        delta (dict): A dictionary of field names and their new values.

    Raises:
        ProtectedFieldError: If the delta contains a field not in ALLOWED_DELTA_FIELDS.
"""
def update_context(context: BookingContext, delta: dict) -> None:
    return update_context_internal(context, delta)


"""
    Recursively serializes complex objects (dicts, lists, dataclasses, pydantic models) 
    into JSON-serializable basic types.

    Args:
        obj (Any): The object to serialize.

    Returns:
        Any: A JSON-serializable representation of the object.
"""
def _serialize_obj(obj: Any) -> Any:
    return _serialize_obj_internal(obj)


"""
    Converts a BookingContext instance into a plain dictionary suitable for JSON serialization.
    Dates are converted to ISO 8601 strings.

    Args:
        context (BookingContext): The context to serialize.

    Returns:
        dict: The serialized context data.
"""
def context_to_dict(context: BookingContext) -> dict:
    return context_to_dict_internal(context)


"""
    Creates a new BookingContext instance from a raw dictionary of data.
    Fields are coerced to their expected types. Deserialization failures result in
    the field being set to None and an error being logged.

    Args:
        data (dict): The raw dictionary data to deserialize.

    Returns:
        BookingContext: A populated BookingContext instance.
"""
def dict_to_context(data: dict) -> BookingContext:
    return dict_to_context_internal(data)
