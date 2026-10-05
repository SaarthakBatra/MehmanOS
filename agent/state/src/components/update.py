"""
Logic for safely updating the BookingContext with validation.
"""
from agent.state.src.components.models import BookingContext, ALLOWED_DELTA_FIELDS, ProtectedFieldError
from agent.state.src.components.coercion import _coerce_value


def update_context(context: BookingContext, delta: dict) -> None:
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
    # Enforce security boundary before processing any updates
    for key in delta.keys():
        if key not in ALLOWED_DELTA_FIELDS:
            raise ProtectedFieldError(f"Field '{key}' is not in ALLOWED_DELTA_FIELDS")
            
    # Process approved delta fields sequentially
    for key, value in delta.items():
        try:
            coerced_val = _coerce_value(key, value)
            setattr(context, key, coerced_val)
        except ValueError as e:
            import agent.state.src.state
            agent.state.src.state.log_error(
                payload={"field": key, "invalid_value": value, "reason": str(e)},
                event_type="ERR_STATE_COERCION_FAILED"
            )
