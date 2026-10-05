import json
import sqlite3
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def check_availability(property_id: str = None, room_id: str = None, check_in: str = None, check_out: str = None, **kwargs) -> str:
    """
    Checks if a specific room in a property is available for a given date range.
    
    Args:
        property_id (str): The identifier of the property (e.g., "GOA001").
        room_id (str): The identifier of the room (e.g., "ROOM_1").
        check_in (str): The desired check-in date in "YYYY-MM-DD" format.
        check_out (str): The desired check-out date in "YYYY-MM-DD" format.
        **kwargs: Optional keyword arguments for test injection (e.g., `_data_path`, `_db_path`).
        
    Returns:
        str: A JSON-encoded string detailing the availability status, any unavailable dates, 
             the minimum remaining rooms, and potentially alternative dates if unavailable. 
             Validation and system errors are also returned as structured JSON strings.
    """
    try:
        # Validate that all required positional arguments are provided.
        if any(x is None for x in [property_id, room_id, check_in, check_out]):
            return json.dumps({
                "error": "ERR_AVAILABILITY_INVALID_ARGUMENTS",
                "code": "ERR_AVAILABILITY_INVALID_ARGUMENTS",
                "message": "Missing required arguments. You must provide property_id, room_id, check_in, and check_out."
            })

        # Validate that all primary inputs are strictly strings.
        if not all(isinstance(x, str) for x in [property_id, room_id, check_in, check_out]):
            return json.dumps({
                "error": "ERR_AVAILABILITY_INVALID_ARGUMENTS",
                "code": "ERR_AVAILABILITY_INVALID_ARGUMENTS",
                "message": "Invalid type. property_id, room_id, check_in, and check_out must be strings."
            })

        # Capture unexpected kwargs to support LLM self-correction.
        # Ignore test-injected paths.
        unexpected_kwargs = [k for k in kwargs if k not in ('_data_path', '_db_path')]
        warning_msg = None
        if unexpected_kwargs:
            logger.warning(f"check_availability received unexpected kwargs: {unexpected_kwargs}")
            warning_msg = f"Unsupported arguments ignored: {unexpected_kwargs}"

        # Resolve database path, prioritizing injected paths for testing over environment/config defaults.
        db_path_str = kwargs.get('_db_path') or kwargs.get('_data_path')
        if db_path_str:
            db_path = Path(db_path_str)
        else:
            settings = get_settings()
            db_path = settings.db_path
            
        if not db_path or not getattr(db_path, "exists", lambda: False)():
            return json.dumps({
                "error": "ERR_AVAILABILITY_DATA_MISSING",
                "code": "ERR_AVAILABILITY_DATA_MISSING",
                "message": "Missing DB_PATH configuration."
            })

        # Parse and validate dates.
        try:
            ci_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            co_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        except ValueError:
            return json.dumps({
                "error": "ERR_AVAILABILITY_INVALID_DATE_FORMAT",
                "code": "ERR_AVAILABILITY_INVALID_DATE_FORMAT",
                "message": "I'm sorry, I didn't catch those dates correctly. Could you repeat them?"
            })
        
        # Explicitly format dates to ensure standardized strings for SQLite comparisons.
        ci_str = ci_date.strftime("%Y-%m-%d")
        co_str = co_date.strftime("%Y-%m-%d")

        # Ensure logical chronological order.
        if co_date <= ci_date:
            return json.dumps({
                "error": "ERR_AVAILABILITY_DATE_RANGE_INVALID",
                "code": "ERR_AVAILABILITY_DATE_RANGE_INVALID",
                "message": "It looks like the checkout date is before or on the check-in date. Could you confirm your dates?"
            })

        # Enforce maximum stay length constraints.
        duration = (co_date - ci_date).days
        if duration > 30:
            return json.dumps({
                "error": "ERR_AVAILABILITY_STAY_TOO_LONG",
                "code": "ERR_AVAILABILITY_STAY_TOO_LONG",
                "message": "Maximum length of stay is 30 nights."
            })

        # Normalize identifiers.
        property_id = property_id.upper()
        room_id = room_id.upper()

        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Pre-flight check: Verify that the room mathematically/physically exists at the property.
            cursor.execute('SELECT 1 FROM availability WHERE property_id = ? AND room_id = ? LIMIT 1', (property_id, room_id))
            if not cursor.fetchone():
                return json.dumps({
                    "error": "ERR_AVAILABILITY_INVALID_ROOM",
                    "code": "ERR_AVAILABILITY_INVALID_ROOM",
                    "message": "I couldn't find that room at the requested property."
                })

            # Primary Query: Fetch all availability records within the requested date window.
            cursor.execute('''
                SELECT date, is_available, remaining_rooms 
                FROM availability 
                WHERE property_id = ? AND room_id = ? AND date >= ? AND date < ? 
                ORDER BY date ASC
            ''', (property_id, room_id, ci_str, co_str))
            
            rows = cursor.fetchall()
            
            # Map retrieved rows for O(1) lookup.
            found_dates = {row['date']: row for row in rows}
            expected_dates = [(ci_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
            
            unavailable_dates = []
            min_remaining = None
            
            # Audit every night of the intended stay. Missing rows implicitly mean unavailable.
            for ed in expected_dates:
                if ed not in found_dates or found_dates[ed]['is_available'] == 0:
                    unavailable_dates.append(ed)
                else:
                    rm = found_dates[ed]['remaining_rooms']
                    if min_remaining is None or rm < min_remaining:
                        min_remaining = rm
            
            # If perfectly contiguous availability exists, return the success payload.
            if not unavailable_dates:
                result = {
                    "available": True,
                    "unavailable_dates": [],
                    "minimum_remaining_rooms": min_remaining,
                    "suggestion": None
                }
                if warning_msg:
                    result["warnings"] = [warning_msg]
                return json.dumps(result)
            
            # Secondary Query: Look ahead for the next available block of equivalent duration.
            max_start_date = ci_date + timedelta(days=30)
            
            cursor.execute('''
                SELECT date, is_available, remaining_rooms 
                FROM availability 
                WHERE property_id = ? AND room_id = ? AND date >= ? 
                ORDER BY date ASC
            ''', (property_id, room_id, ci_str))
            
            all_future_rows = cursor.fetchall()
            future_dict = {row['date']: row for row in all_future_rows}
            
            suggestion = None
            if all_future_rows:
                # Scan all possible future start dates within the 30-day lookahead window.
                start_dates = [datetime.strptime(row['date'], "%Y-%m-%d").date() for row in all_future_rows if row['is_available'] == 1]
                
                for sd in start_dates:
                    if sd > max_start_date:
                        break
                        
                    block_available = True
                    block_min_rm = None
                    block_dates = [(sd + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
                    
                    # Verify contiguous availability for the candidate block.
                    for bd in block_dates:
                        if bd not in future_dict or future_dict[bd]['is_available'] == 0:
                            block_available = False
                            break
                        rm = future_dict[bd]['remaining_rooms']
                        if block_min_rm is None or rm < block_min_rm:
                            block_min_rm = rm
                    
                    if block_available:
                        suggestion = {
                            "alternative_room_id": room_id,
                            "alternative_dates": {
                                "check_in": sd.strftime("%Y-%m-%d"),
                                "check_out": (sd + timedelta(days=duration)).strftime("%Y-%m-%d")
                            },
                            "minimum_remaining_rooms": block_min_rm
                        }
                        break
            
            # Return failure payload including the unavailable dates and potential suggestion.
            result = {
                "available": False,
                "unavailable_dates": unavailable_dates,
                "minimum_remaining_rooms": None,
                "suggestion": suggestion
            }
            if warning_msg:
                result["warnings"] = [warning_msg]
            return json.dumps(result)
            
        finally:
            conn.close()

    except sqlite3.Error as e:
        # Differentiate between recoverable lock timeouts and catastrophic data loss.
        if "database is locked" in str(e).lower():
            return json.dumps({
                "error": "ERR_AVAILABILITY_DB_LOCKED",
                "code": "ERR_AVAILABILITY_DB_LOCKED",
                "message": "I'm having trouble checking the availability right now. Let me try again in a moment."
            })
        return json.dumps({
            "error": "ERR_AVAILABILITY_DATA_MISSING",
            "code": "ERR_AVAILABILITY_DATA_MISSING",
            "message": "I'm having trouble accessing the hotel's database right now. Please try again later."
        })
    except Exception:
        # Fallback catch-all for robust tool execution.
        return json.dumps({
            "error": "ERR_AVAILABILITY_DATA_MISSING",
            "code": "ERR_AVAILABILITY_DATA_MISSING",
            "message": "I'm having trouble accessing the hotel's database right now. Please try again later."
        })
