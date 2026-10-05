"""
Provides validation utilities for the session store.
"""
from agent.session_store.src.errors import SessionStoreInvalidIdException


def _validate_session_id(session_id: str) -> None:
    """
    Validates the session_id to prevent path traversal or invalid characters.
    
    Args:
        session_id (str): The session ID to validate.
        
    Raises:
        SessionStoreInvalidIdException: If the session_id contains invalid characters.
    """
    import agent.session_store.src.session_store as router
    
    # Enforce strict alphanumeric format to prevent path traversal attacks
    if not router.re.match(r"^[a-zA-Z0-9_-]+$", session_id):
        raise SessionStoreInvalidIdException(f"Invalid session ID: {session_id}")
