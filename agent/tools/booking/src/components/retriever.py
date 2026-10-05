"""
Component for retrieving bookings by phone or reference.
"""
import json
import logging
import sqlite3
from pathlib import Path
from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def get_booking(lookup_value: str = None, lookup_type: str = 'phone', **kwargs) -> str:
    """
    Retrieve existing bookings by phone number or booking reference.

    Args:
        lookup_value (str): The phone number or booking reference to search for.
        lookup_type (str): The type of lookup ('phone' or 'ref'). Defaults to 'phone'.
        **kwargs: Injected dependencies for testing and system context (_db_path).

    Returns:
        str: A JSON-encoded string containing a list of booking details or an error payload.
    """
    db_path_str = kwargs.get("_db_path")
    settings = get_settings()
    db_path = Path(db_path_str) if db_path_str else settings.db_path
    
    try:
        if not lookup_value:
            return json.dumps({"error": "ERR_BOOKING_MISSING_PARAMETER", "message": "Missing lookup_value parameter."})
        
        # Enforce DML guards
        dml_keywords = ["DROP ", "DELETE ", "UPDATE ", "ALTER ", "TRUNCATE ", "EXEC "]
        if isinstance(lookup_value, str):
            param_upper = lookup_value.upper()
            if any(kw in param_upper for kw in dml_keywords):
                return json.dumps({"error": "ERR_BOOKING_DML_GUARD_VIOLATION", "message": "The system blocked the request due to a potential security violation in the parameters."})

        # Connect to DB and fetch rows by lookup type
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        if lookup_type == 'phone':
            cur.execute("SELECT * FROM bookings WHERE guest_phone = ?", (lookup_value,))
        elif lookup_type == 'ref':
            cur.execute("SELECT * FROM bookings WHERE booking_ref = ?", (lookup_value,))
        else:
            conn.close()
            return json.dumps({"error": "ERR_BOOKING_INVALID_PARAMETER", "message": "Invalid lookup_type parameter. Must be 'phone' or 'ref'."})
            
        rows = cur.fetchall()
        conn.close()
        
        # Load properties data safely to enrich response with human-readable names
        try:
            properties_path = settings.properties_path
            with open(properties_path, "r") as f:
                properties = json.load(f)
        except Exception:
            properties = []

        # If add_ons is stored as JSON string, parse it back to list
        result = []
        for row in rows:
            row_dict = dict(row)
            if 'add_ons' in row_dict and isinstance(row_dict['add_ons'], str):
                try:
                    row_dict['add_ons'] = json.loads(row_dict['add_ons'])
                except Exception:
                    pass
            
            # Enrich with property and room names
            prop_data = next((p for p in properties if p["property_id"] == row_dict.get("property_id")), None)
            if prop_data:
                row_dict["property_name"] = prop_data.get("name")
                room_data = next((r for r in prop_data.get("room_types", []) if r["room_id"] == row_dict.get("room_id")), None)
                if room_data:
                    row_dict["room_name"] = room_data.get("name")

            result.append(row_dict)
            
        return json.dumps(result)
        
    except Exception as e:
        logger.error(f"Failed to get booking: {e}")
        return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the request."})
