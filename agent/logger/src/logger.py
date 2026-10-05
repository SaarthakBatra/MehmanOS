"""
Router for the logger module.

Exposes the public logging interfaces by delegating to the underlying components.
"""
from typing import Any
from .components import core
from .components import logging_methods
from .components.context import session_context

"""
    Initializes the logging configuration.

    This function configures the root logger to output structured JSON logs.
    It manages the creation of file handlers per session and a standard output handler.
    It is idempotent and can be safely called multiple times.

    Args:
        debug (bool): If True, allows DEBUG level logs to be printed to stdout. 
                      If False, suppresses DEBUG level logs on stdout. 
                      Note that file logs will always capture DEBUG logs regardless of this flag.
    """
def setup_logger(debug: bool) -> None:
    return core.setup_logger(debug)

"""
    Emits a structured JSON log entry with level "INFO".

    This is the standard logging method for informational events in the system.
    If the logger has not been explicitly initialized via `setup_logger`, this function 
    will lazily initialize it with `debug=False`.

    Args:
        event_type (str): A string identifier for the event (e.g., 'TOOL_CALL').
        payload (dict[str, Any]): A dictionary of context or data to log. If a non-dict 
                                  is provided, it will be gracefully coerced into a dict.
        session_id (str | None): Optional session tracking identifier. If omitted, the 
                                 current context's session_id will be used if available.
    """
def log_info(event_type: str, payload: dict[str, Any], session_id: str | None = None) -> None:
    return logging_methods.log_info(event_type, payload, session_id)

"""
    Emits a structured JSON log entry with level "DEBUG".

    Use this for verbose tracing and debugging information. These logs will only be 
    emitted to stdout if the logger was initialized with `debug=True`.
    If the logger has not been explicitly initialized via `setup_logger`, this function 
    will lazily initialize it with `debug=False`.

    Args:
        event_type (str): A string identifier for the event.
        payload (dict[str, Any]): A dictionary of context or data to log.
        session_id (str | None): Optional session tracking identifier.
    """
def log_debug(event_type: str, payload: dict[str, Any], session_id: str | None = None) -> None:
    return logging_methods.log_debug(event_type, payload, session_id)

"""
    Emits an error-level JSON log entry.

    Use this to log exceptions and systemic failures. These logs are always emitted.
    If the logger has not been explicitly initialized via `setup_logger`, this function 
    will lazily initialize it with `debug=False`.

    Args:
        payload (dict[str, Any]): A dictionary of context/data describing the error.
        event_type (str, optional): A string identifier for the event category. Defaults to "SYSTEM_ERROR".
        session_id (str | None): Optional session tracking identifier.
    """
def log_error(payload: dict[str, Any], event_type: str = "SYSTEM_ERROR", session_id: str | None = None) -> None:
    return logging_methods.log_error(payload, event_type, session_id)

"""
    Resets the logger state for testing environments to prevent state bleed.
    
    This function removes all handlers and resets the initialization flag.
    It should strictly be used within test teardown blocks.
    """
def _reset_logger() -> None:
    return core._reset_logger()
