"""
Public logging methods to emit JSON logs at various levels.
"""
from typing import Any
from .core import _ensure_initialized, _get_logger
from .entry_builder import _build_log_entry

def log_info(event_type: str, payload: dict[str, Any], session_id: str | None = None) -> None:
    """
    Emits a structured JSON log entry with level "INFO".

    Args:
        event_type (str): A string identifier for the event.
        payload (dict[str, Any]): A dictionary of context/data to log.
        session_id (str | None): Optional session tracking identifier.
    """
    # Lazily ensure the logger is initialized (defaults to debug=False if not explicitly set)
    _ensure_initialized()
    logger = _get_logger()
    entry: dict[str, Any] = _build_log_entry("INFO", event_type, payload, session_id)
    logger.info(entry)

def log_debug(event_type: str, payload: dict[str, Any], session_id: str | None = None) -> None:
    """
    Emits a structured JSON log entry with level "DEBUG".

    Args:
        event_type (str): A string identifier for the event.
        payload (dict[str, Any]): A dictionary of context/data to log.
        session_id (str | None): Optional session tracking identifier.
    """
    # Lazily ensure the logger is initialized (defaults to debug=False if not explicitly set)
    _ensure_initialized()
    logger = _get_logger()
    # Always emit to logger.debug; the underlying StreamHandler level configuration will filter it if debug=False
    entry: dict[str, Any] = _build_log_entry("DEBUG", event_type, payload, session_id)
    logger.debug(entry)

def log_error(payload: dict[str, Any], event_type: str = "SYSTEM_ERROR", session_id: str | None = None) -> None:
    """
    Emits an error-level JSON log entry.

    Args:
        payload (dict[str, Any]): A dictionary of context/data to log.
        event_type (str, optional): A string identifier for the event. Defaults to "SYSTEM_ERROR".
        session_id (str | None): Optional session tracking identifier.
    """
    # Lazily ensure the logger is initialized (defaults to debug=False if not explicitly set)
    _ensure_initialized()
    logger = _get_logger()
    entry: dict[str, Any] = _build_log_entry("ERROR", event_type, payload, session_id)
    logger.error(entry)
