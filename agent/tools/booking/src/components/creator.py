"""
Component for creating and managing booking holds.
"""
import json
import logging
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def create_booking_hold(
    property_id: str = None,
    room_id: str = None,
    check_in: str = None,
    check_out: str = None,
    guests: int = None,
    guest_name: str = None,
    guest_phone: str = None,
    add_on_ids: list[str] | None = None,
    **kwargs
) -> str:
    """
    Create a temporary booking hold for a specific property and room.

    Validates inputs, ensures availability, calculates the total price,
    and inserts a new booking record into the database with a 'hold' status.

    Args:
        property_id (str): The unique identifier for the property.
        room_id (str): The unique identifier for the room type.
        check_in (str): Check-in date in YYYY-MM-DD format.
        check_out (str): Check-out date in YYYY-MM-DD format.
        guests (int): Number of guests for the booking.
        guest_name (str): The primary guest's full name.
        guest_phone (str): The primary guest's contact phone number.
        add_on_ids (list[str] | None): Optional list of add-on identifiers.
        **kwargs: Injected dependencies for testing and system context
            (_data_path, _db_path, _system_date, _check_availability_func,
            _calculate_price_func, _uuid_func).

    Returns:
        str: A JSON-encoded string containing either the booking hold details
             or an error payload with an error code and message.
    """
    data_path_str = kwargs.get("_data_path")
    db_path_str = kwargs.get("_db_path")
    _system_date = kwargs.get("_system_date")
    _check_availability_func = kwargs.get("_check_availability_func")
    _calculate_price_func = kwargs.get("_calculate_price_func")
    _uuid_func = kwargs.get("_uuid_func")
    
    settings = get_settings()
    properties_path = Path(data_path_str) if data_path_str else settings.properties_path
    db_path = Path(db_path_str) if db_path_str else settings.db_path
    
    expected_injected = {"_data_path", "_db_path", "_system_date", "_check_availability_func", "_calculate_price_func", "_uuid_func"}
    unexpected_kwargs = [k for k in kwargs if k not in expected_injected]
    
    warnings = []
    # Collect warnings for hallucinated LLM arguments
    if unexpected_kwargs:
        logger.warning(f"Unexpected parameters ignored: {unexpected_kwargs}")
        warnings.append(f"Ignored unexpected parameters: {unexpected_kwargs}")

    try:
        # Validate that all required parameters are provided
        if any(x is None for x in [property_id, room_id, check_in, check_out, guests, guest_name, guest_phone]):
            return json.dumps({"error": "ERR_BOOKING_MISSING_PARAMETER", "message": "Missing required arguments. You must provide property_id, room_id, check_in, check_out, guests, guest_name, and guest_phone."})

        # Basic type and format validations
        if not all(isinstance(x, str) for x in [property_id, room_id]):
            return json.dumps({"error": "ERR_BOOKING_INVALID_ROOM", "message": "The property_id or room_id is invalid or could not be found in the system data."})

        if not all(isinstance(x, str) for x in [check_in, check_out]):
            return json.dumps({"error": "ERR_BOOKING_INVALID_DATE_FORMAT", "message": "The check_in or check_out dates are invalid or not in the YYYY-MM-DD format."})
        
        if not isinstance(guests, int) or guests < 1:
            return json.dumps({"error": "ERR_BOOKING_INVALID_GUESTS", "message": "The guests argument must be an integer greater than or equal to 1."})

        if not isinstance(guest_name, str) or not guest_name.strip():
            return json.dumps({"error": "ERR_BOOKING_INVALID_NAME", "message": "The guest_name argument must be a non-empty string."})
            
        if not isinstance(guest_phone, str) or not guest_phone.strip():
            return json.dumps({"error": "ERR_BOOKING_MISSING_PARAMETER", "message": "The guest_phone argument must be a non-empty string."})

        if add_on_ids is not None:
            if not isinstance(add_on_ids, list) or not all(isinstance(x, str) for x in add_on_ids):
                return json.dumps({"error": "ERR_BOOKING_INVALID_ADDONS_FORMAT", "message": "The add_on_ids argument must be a list of strings if provided."})

        # Load properties data safely
        try:
            with open(properties_path, "r") as f:
                properties = json.load(f)
        except Exception:
            return json.dumps({"error": "ERR_BOOKING_INVALID_ROOM", "message": "The property_id or room_id is invalid or could not be found in the system data."})

        property_data = next((p for p in properties if p["property_id"] == property_id), None)
        if not property_data:
            return json.dumps({"error": "ERR_BOOKING_INVALID_ROOM", "message": "The property_id or room_id is invalid or could not be found in the system data."})
            
        room_data = next((r for r in property_data.get("room_types", []) if r["room_id"] == room_id), None)
        if not room_data:
            return json.dumps({"error": "ERR_BOOKING_INVALID_ROOM", "message": "The property_id or room_id is invalid or could not be found in the system data."})

        # Verify capacity constraints
        capacity = room_data.get("capacity", 0)
        if guests > capacity:
            return json.dumps({"error": "ERR_BOOKING_CAPACITY_EXCEEDED", "message": "The number of guests exceeds the maximum capacity of the requested room."})

        # Validate date formats and logic
        try:
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
        except ValueError:
            return json.dumps({"error": "ERR_BOOKING_INVALID_DATE_FORMAT", "message": "The check_in or check_out dates are invalid or not in the YYYY-MM-DD format."})

        if check_out_date <= check_in_date:
            return json.dumps({"error": "ERR_BOOKING_INVALID_DATES", "message": "The check_out date must be strictly after the check_in date."})

        system_date = _system_date or date.today()
        if check_in_date < system_date:
            return json.dumps({"error": "ERR_BOOKING_PAST_DATE", "message": "The check_in date cannot be in the past."})

        # Validate availability using the injected function
        if _check_availability_func:
            avail_res_str = _check_availability_func(property_id=property_id, room_id=room_id, check_in=check_in, check_out=check_out, _db_path=str(db_path))
            try:
                avail_res = json.loads(avail_res_str)
            except Exception:
                return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})
                
            if "error" in avail_res:
                return avail_res_str  # Bubble up any upstream errors
            if not avail_res.get("available", False):
                return json.dumps({"error": "ERR_BOOKING_UNAVAILABLE", "message": "The requested room is not available for the specified dates."})
        else:
            return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})

        # Calculate final price using the injected function
        if _calculate_price_func:
            price_res_str = _calculate_price_func(property_id=property_id, room_id=room_id, check_in=check_in, check_out=check_out, add_on_ids=add_on_ids, _data_path=str(properties_path))
            try:
                price_res = json.loads(price_res_str)
            except Exception:
                return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})
            if "error" in price_res:
                return price_res_str  # Bubble up any upstream errors
            total_price = price_res.get("total", price_res.get("total_price", 0))
        else:
            return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})

        query = "INSERT INTO bookings (booking_ref, property_id, room_id, check_in, check_out, guests, guest_name, guest_phone, add_ons, total_price, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        
        # Enforce DML guards to prevent SQL injection or malicious manipulation
        query_upper = query.upper().strip()
        if not query_upper.startswith("INSERT INTO BOOKINGS"):
            return json.dumps({"error": "ERR_BOOKING_DML_GUARD_VIOLATION", "message": "The system blocked the request due to a potential security violation in the parameters."})
            
        dml_keywords = ["DROP ", "DELETE ", "UPDATE ", "ALTER ", "TRUNCATE ", "EXEC "]
        for param in [property_id, room_id, check_in, check_out, guest_name, guest_phone] + (add_on_ids or []):
            if isinstance(param, str):
                param_upper = param.upper()
                if any(kw in param_upper for kw in dml_keywords):
                    return json.dumps({"error": "ERR_BOOKING_DML_GUARD_VIOLATION", "message": "The system blocked the request due to a potential security violation in the parameters."})
            
        booking_ref = f"MHM-{str(_uuid_func() if _uuid_func else uuid.uuid4())[:8].upper()}"
        add_ons_json = json.dumps(add_on_ids) if add_on_ids else json.dumps([])
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            conn = sqlite3.connect(db_path)
        except Exception:
            return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})
            
        try:
            cur = conn.cursor()
            # Prevent duplicate bookings by checking identical details
            cur.execute("SELECT 1 FROM bookings WHERE property_id=? AND room_id=? AND check_in=? AND check_out=? AND guest_name=? AND guest_phone=? AND status != 'cancelled'", (property_id, room_id, check_in, check_out, guest_name, guest_phone))
            if cur.fetchone():
                conn.close()
                return json.dumps({"error": "ERR_BOOKING_DUPLICATE", "message": "An identical booking hold already exists in the system."})
                
            cur.execute(query, (booking_ref, property_id, room_id, check_in, check_out, guests, guest_name, guest_phone, add_ons_json, total_price, 'hold', created_at))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            return json.dumps({"error": "ERR_BOOKING_DATA_INTEGRITY_VIOLATION", "message": "The booking could not be saved due to a database integrity violation."})
        except Exception:
            conn.rollback()
            return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})
        finally:
            conn.close()

        payload = {
            "booking_ref": booking_ref,
            "property_name": property_data.get("name"),
            "room_name": room_data.get("name"),
            "check_in": check_in,
            "check_out": check_out,
            "total_price": total_price,
            "status": "hold",
            "valid_for": "24 hours"
        }
        if warnings:
            payload["warnings"] = warnings
        return json.dumps(payload)

    except Exception:
        return json.dumps({"error": "ERR_BOOKING_SYSTEM_FAILURE", "message": "An internal system failure occurred while processing the booking."})
