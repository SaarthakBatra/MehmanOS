"""
Provides functionality to safely delete a session's JSON file.
"""
from agent.session_store.src.errors import (
    SessionStoreLockTimeoutException,
    SessionStoreWriteException
)
from agent.session_store.src.components.validator import _validate_session_id


def delete_context(session_id: str) -> None:
    """
    Safely deletes the session's JSON file from disk.
    
    Args:
        session_id (str): The unique session identifier.
        
    Raises:
        SessionStoreInvalidIdException: If the session_id is invalid.
        SessionStoreLockTimeoutException: If the file lock cannot be acquired.
        SessionStoreWriteException: If the file exists but cannot be deleted.
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
            # Operation is idempotent; succeed silently if the file is already gone
            if not file_path.exists():
                return
            
            try:
                router.os.remove(file_path)
            except OSError as e:
                raise SessionStoreWriteException(f"Delete failed: {e}")
        finally:
            lock.release()
    except router.Timeout:
        raise SessionStoreLockTimeoutException("Lock timeout on delete")

