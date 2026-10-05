"""
Component for cancelling active bookings.
"""
import json
import logging
import sqlite3
from pathlib import Path
from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def cancel_booking(booking_ref: str = None, **kwargs) -> str:
    """
    Cancel an existing booking.

    Args:
        booking_ref (str): The unique booking reference to cancel.
        **kwargs: Injected dependencies for testing and system context (_db_path).

    Returns:
        str: A JSON-encoded string containing the result of the cancellation or an error payload.
    """
    db_path_str = kwargs.get("_db_path")
    settings = get_settings()
    db_path = Path(db_path_str) if db_path_str else settings.db_path
    
    try:
        if not booking_ref:
            return json.dumps({"error": "ERR_BOOKING_MISSING_PARAMETER", "message": "Missing booking_ref parameter."})
        
        # Enforce DML guards
        query = "UPDATE bookings SET status = 'cancelled' WHERE booking_ref = ? AND status != 'cancelled'"
        query_upper = query.upper().strip()
        if not query_upper.startswith("UPDATE BOOKINGS SET STATUS = 'CANCELLED'"):
            return json.dumps({"error": "ERR_BOOKING_DML_GUARD_VIOLATION", "message": "The system blocked the request due to a potential security violation in the parameters."})

        dml_keywords = ["DROP ", "DELETE ", "UPDATE ", "ALTER ", "TRUNCATE ", "EXEC "]
        if isinstance(booking_ref, str):
            param_upper = booking_ref.upper()
            if any(kw in param_upper for kw in dml_keywords):
                return json.dumps({"error": "ERR_BOOKING_DML_GUARD_VIOLATION", "message": "The system blocked the request due to a potential security violation in the parameters."})

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Execute cancellation update
        cur.execute(query, (booking_ref,))
        if cur.rowcount == 0:
            conn.rollback()
            conn.close()
            return json.dumps({"error": "ERR_BOOKING_NOT_FOUND", "message": "Booking not found or already cancelled."})
            
        conn.commit()
        conn.close()
        
        return json.dumps({"status": "success", "message": "Booking successfully cancelled."})
        
    except Exception as e:
        logger.error(f"Failed to cancel booking: {e}")
        return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the request."})
