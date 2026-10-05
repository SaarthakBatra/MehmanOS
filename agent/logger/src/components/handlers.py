"""
Custom logging handlers, including file routing per session.
"""
import logging
import os
from .formatters import JsonFormatter
from .context import session_context

class SessionFileHandler(logging.Handler):
    """
    A custom logging handler that routes logs to separate files based on the session_id.
    Ensures that concurrent Streamlit sessions have isolated log trails.
    """
    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.formatter = JsonFormatter()
        os.makedirs(self.base_dir, exist_ok=True)
        # Dictionary to store file handlers mapped by session_id
        self.file_handlers: dict[str, logging.FileHandler] = {}

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.msg
            # Extract session_id from dictionary messages, otherwise fallback to context
            if isinstance(msg, dict):
                session_id = msg.get("session_id", session_context.get())
            else:
                session_id = session_context.get()
                
            # Lazily instantiate file handlers per session to isolate log trails
            if session_id not in self.file_handlers:
                filepath = os.path.join(self.base_dir, f"{session_id}_logs.logs")
                fh = logging.FileHandler(filepath)
                fh.setFormatter(self.formatter)
                self.file_handlers[session_id] = fh
                
            self.file_handlers[session_id].emit(record)
        except Exception:
            self.handleError(record)
