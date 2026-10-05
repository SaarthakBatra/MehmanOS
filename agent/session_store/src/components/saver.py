"""
Provides functionality to save a BookingContext to a JSON file.
"""
from agent.state.src.state import BookingContext
from agent.session_store.src.errors import (
    SessionStoreWriteException,
    SessionStoreLockTimeoutException
)
from agent.session_store.src.components.validator import _validate_session_id


def save_context(session_id: str, context: BookingContext) -> None:
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
    import agent.session_store.src.session_store as router
    
    _validate_session_id(session_id)
    settings = router.get_settings()
    session_dir = router.Path(settings.session_dir)
    
    # Ensure the session directory hierarchy exists
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise SessionStoreWriteException(f"Failed to create session directory: {e}")
        
    file_path = session_dir / f"{session_id}.json"
    lock_path = session_dir / f"{session_id}.json.lock"
    
    lock = router.FileLock(lock_path, timeout=settings.session_lock_timeout)
    
    try:
        lock.acquire()
        try:
            # Delegate complex type serialization to the state module
            data = router.context_to_dict(context)
            tmp_path = session_dir / f"{session_id}.json.tmp"
            
            # Atomic write: Write to a temp file and rename to prevent corruption
            try:
                with open(tmp_path, "w", encoding="utf-8") as f:
                    router.json.dump(data, f)
                router.os.rename(tmp_path, file_path)
            except OSError as e:
                raise SessionStoreWriteException(f"Write failed: {e}")
            finally:
                # Cleanup the temporary file if the atomic rename failed
                if tmp_path.exists():
                    try:
                        router.os.remove(tmp_path)
                    except OSError:
                        pass
        finally:
            lock.release()
    except router.Timeout:
        raise SessionStoreLockTimeoutException("Lock timeout on save")

