"""
Context variable definitions for the logger module.
"""
import contextvars

# ContextVar used to track and isolate log streams per concurrent session.
session_context: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="system")
