"""
Router for the prompt_builder module.
"""
from .components.encoders import _date_encoder as __date_encoder
from .components.builder import build_system_prompt as _build_system_prompt

"""
JSON encoder function for serializing datetime objects.

Args:
    obj: The object to serialize.
    
Returns:
    str: The ISO 8601 string representation if the object is a datetime or date.
    
Raises:
    TypeError: If the object is not a supported datetime type.
"""
def _date_encoder(obj):
    return __date_encoder(obj)

"""
Builds the complete system prompt for the AI assistant by combining the persona,
rules, booking context, and tool usage policies.

Args:
    booking_context (Optional[dict]): The current state of the booking, containing fields like destination and dates.
    intent_hints (str): Pre-computed intent signals to guide the LLM's response.
    system_date (str): The current system date for temporal grounding.

Returns:
    str: The fully assembled system prompt.

Raises:
    TypeError: If booking_context is not a dictionary or None.
    ValueError: If serialization of the safe context fails.
"""
def build_system_prompt(booking_context: dict | None = None, intent_hints: str = "", system_date: str = "") -> str:
    return _build_system_prompt(booking_context, intent_hints, system_date)
