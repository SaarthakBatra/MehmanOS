import os
import json
import re
from pathlib import Path
from filelock import FileLock, Timeout

from agent.state.src.state import BookingContext, context_to_dict, dict_to_context
from agent.config.src.config import get_settings
from agent.session_store.src.errors import (
    SessionStoreInvalidIdException,
    SessionStoreLockTimeoutException,
    SessionStoreReadException,
    SessionStoreWriteException
)

from agent.session_store.src.components import saver
from agent.session_store.src.components import loader
from agent.session_store.src.components import deleter
from agent.session_store.src.components import validator

"""
Validates the session_id to prevent path traversal or invalid characters.

Args:
    session_id (str): The session ID to validate.
    
Raises:
    SessionStoreInvalidIdException: If the session_id contains invalid characters.
"""
def _validate_session_id(session_id: str) -> None:
    return validator._validate_session_id(session_id)

"""
Serializes a BookingContext object and saves it to a JSON file.

Args:
    session_id (str): The unique session identifier.
    context (BookingContext): The context to save.
    
Raises:
    SessionStoreInvalidIdException: If the session_id is invalid.
    SessionStoreWriteException: If creating the directory or writing the file fails.
    SessionStoreLockTimeoutException: If the file lock cannot be acquired.
"""
def save_context(session_id: str, context: BookingContext) -> None:
    return saver.save_context(session_id, context)

"""
Loads a BookingContext from the session's JSON file.

Args:
    session_id (str): The unique session identifier.
    
Returns:
    BookingContext: The loaded context, or a new empty context if the file does not exist.
    
Raises:
    SessionStoreInvalidIdException: If the session_id is invalid.
    SessionStoreLockTimeoutException: If the file lock cannot be acquired.
    SessionStoreReadException: If the file cannot be read or parsed correctly.
"""
def load_context(session_id: str) -> BookingContext:
    return loader.load_context(session_id)

"""
Safely deletes the session's JSON file from disk.

Args:
    session_id (str): The unique session identifier.
    
Raises:
    SessionStoreInvalidIdException: If the session_id is invalid.
    SessionStoreLockTimeoutException: If the file lock cannot be acquired.
    SessionStoreWriteException: If the file exists but cannot be deleted.
"""
def delete_context(session_id: str) -> None:
    return deleter.delete_context(session_id)
