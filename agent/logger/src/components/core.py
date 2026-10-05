"""
Core initialization and configuration functions for the logger.
"""
import logging
import os
import sys
import agent.config.src.config as config_mod
from .formatters import JsonFormatter
from .handlers import SessionFileHandler

_is_initialized: bool = False

def _get_logger() -> logging.Logger:
    """Retrieves the dedicated named logger for the agent."""
    return logging.getLogger("mehman")

def setup_logger(debug: bool) -> None:
    """
    Initializes the logging configuration.

    Args:
        debug (bool): If True, allows DEBUG level logs. If False, suppresses DEBUG level logs.
    """
    global _is_initialized
    logger = _get_logger()
    logger.propagate = False
    logger.setLevel(logging.DEBUG)  # Root logger catches everything
    
    # Idempotency: clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(handler)
    
    # Navigate 5 directories up from src/components/core.py to reach the project root for the 'sessions' folder
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))), "sessions")
    file_handler = SessionFileHandler(base_dir)
    file_handler.setLevel(logging.DEBUG)  # Always capture full traces in files
    logger.addHandler(file_handler)
    
    _is_initialized = True

def _ensure_initialized() -> None:
    """Lazily auto-initializes the logger if it hasn't been explicitly set up."""
    global _is_initialized
    if not _is_initialized:
        try:
            # Attempt to fetch settings dynamically; critical for tests that might mock get_settings
            config = config_mod.get_settings()
            debug_val = config.debug
        except Exception:
            # Fallback to False if the config cannot be loaded
            debug_val = False
        setup_logger(debug=debug_val)

def _reset_logger() -> None:
    """Resets the logger state for testing environments to prevent state bleed."""
    global _is_initialized
    logger = _get_logger()
    logger.handlers.clear()
    _is_initialized = False
