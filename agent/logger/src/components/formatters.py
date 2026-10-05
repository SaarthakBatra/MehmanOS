"""
JSON encoding and formatting classes for structured logging.
"""
import json
import logging
from typing import Any
from datetime import datetime, timezone
from .context import session_context

class FallbackJSONEncoder(json.JSONEncoder):
    """
    Custom JSONEncoder that falls back to string representation for
    un-serializable objects to prevent logging exceptions.
    """
    def default(self, obj: Any) -> str:
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

class JsonFormatter(logging.Formatter):
    """
    Formatter that emits structured JSON logs. Handles strict encoding
    and gracefully falls back if types are invalid.
    """
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, dict):
            try:
                # Attempt strict json encoding first
                return json.dumps(record.msg)
            except TypeError:
                record.msg["_serialisation_warning"] = True
                return json.dumps(record.msg, cls=FallbackJSONEncoder)
        
        # If it's a standard string log from a third-party or unhandled source, wrap it in our structured format
        entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "event_type": "STANDARD_LOG",
            "payload": {"message": str(record.msg)},
            "session_id": session_context.get()
        }
        return json.dumps(entry)
