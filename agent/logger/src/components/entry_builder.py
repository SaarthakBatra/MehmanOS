"""
Helper functions for building structured log entries.
"""
from datetime import datetime, timezone
from typing import Any

def _build_log_entry(level: str, event_type: str, payload: Any, session_id: str | None = None) -> dict[str, Any]:
    """
    Constructs a structured dictionary for the log entry, coercing types if necessary.

    Args:
        level (str): The log level (e.g., 'INFO', 'DEBUG').
        event_type (str): The string identifier for the event.
        payload (Any): The payload to log. If not a dict, it will be wrapped.
        session_id (str | None): Optional session tracking identifier.

    Returns:
        dict[str, Any]: The fully formatted dictionary ready for JSON serialization.
    """
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "level": level,
        "event_type": event_type,
    }
    
    invalid_type: bool = False
    if not isinstance(payload, dict):
        invalid_type = True
        # Wrap scalar or list payloads in a dictionary to maintain structured JSON constraints
        payload_dict = {"_raw_payload": payload}
    else:
        # Shallow copy to avoid mutating the original payload dictionary
        payload_dict = dict(payload)

    entry["payload"] = payload_dict
    
    if session_id is not None:
        entry["session_id"] = session_id
        
    if invalid_type:
        entry["_invalid_payload_type"] = True
        
    return entry
