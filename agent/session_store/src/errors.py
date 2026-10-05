class SessionStoreInvalidIdException(Exception):
    """Raised when the provided session_id fails validation (e.g., path traversal)."""
    pass

class SessionStoreLockTimeoutException(Exception):
    """Raised when a file lock cannot be acquired within the configured timeout period."""
    pass

class SessionStoreReadException(Exception):
    """Raised when a session file exists but cannot be read or parsed correctly."""
    pass

class SessionStoreWriteException(Exception):
    """Raised when the system fails to write or delete a session file."""
    pass
