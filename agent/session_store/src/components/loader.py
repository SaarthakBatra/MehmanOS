"""
Provides functionality to load a BookingContext from a JSON file.
"""
from agent.state.src.state import BookingContext
from agent.session_store.src.errors import (
    SessionStoreLockTimeoutException,
    SessionStoreReadException
)
from agent.session_store.src.components.validator import _validate_session_id


def load_context(session_id: str) -> BookingContext:
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
    import agent.session_store.src.session_store as router
    
    _validate_session_id(session_id)
    settings = router.get_settings()
    session_dir = router.Path(settings.session_dir)
    file_path = session_dir / f"{session_id}.json"
    lock_path = session_dir / f"{session_id}.json.lock"
    
    lock = router.FileLock(lock_path, timeout=settings.session_lock_timeout)
    try:
        lock.acquire()
        try:
            # Return a fresh, empty context if no prior session file exists on disk
            if not file_path.exists():
                return BookingContext()
            
            # Read JSON safely and delegate schema hydration to the state module
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = router.json.load(f)
                return router.dict_to_context(data)
            except (OSError, router.json.JSONDecodeError, TypeError, ValueError, AttributeError) as e:
                raise SessionStoreReadException(f"Read failed: {e}")
        finally:
            lock.release()
    except router.Timeout:
        raise SessionStoreLockTimeoutException("Lock timeout on load")

