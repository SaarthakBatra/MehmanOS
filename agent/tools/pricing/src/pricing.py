import json
from datetime import date
from pathlib import Path
from agent.config.src.config import get_settings

def calculate_price(
    property_id: str | None = None,
    room_id: str | None = None,
    check_in: str | None = None,
    check_out: str | None = None,
    add_on_ids: list[str] | None = None,
    **kwargs
) -> str:
    """
    Calculates the total price of a booking based on dates, room rates, and add-ons.

    Args:
        property_id (str | None): The ID of the property.
        room_id (str | None): The ID of the specific room type.
        check_in (str | None): Check-in date in ISO format (YYYY-MM-DD).
        check_out (str | None): Check-out date in ISO format (YYYY-MM-DD).
        add_on_ids (list[str] | None): Optional list of add-on IDs requested.
        **kwargs: Absorbs any unexpected or hallucinated arguments to prevent crashes.

    Returns:
        str: A JSON-formatted string containing either the successful pricing breakdown
             or a structured error response payload.
    """
    try:
        # Extract the dependency injected path, if provided
        data_path_str = kwargs.get("_data_path")
        
        # Track unexpected kwargs to allow the LLM to self-correct
        warnings = []
        ignored_keys = [k for k in kwargs.keys() if k != "_data_path"]
        if ignored_keys:
            warnings.append(f"Ignored unexpected arguments: {', '.join(ignored_keys)}")
            
        # Validate that all required core arguments are present
        if any(x is None for x in [property_id, room_id, check_in, check_out]):
            return json.dumps({"error": "ERR_PRICING_INVALID_INPUT", "message": "Missing required arguments. You must provide property_id, room_id, check_in, and check_out."})
        
        # Ensure core string arguments are of the correct type
        if not all(isinstance(x, str) for x in [property_id, room_id, check_in, check_out]):
            return json.dumps({"error": "ERR_PRICING_INVALID_INPUT", "message": "Invalid type. property_id, room_id, check_in, and check_out must be strings."})

        # Validate add_on_ids type if provided
        if add_on_ids is not None and not isinstance(add_on_ids, list):
            return json.dumps({"error": "ERR_PRICING_INVALID_INPUT", "message": f"Invalid type for add_on_ids. Expected a list of strings, but got {type(add_on_ids).__name__}."})
        
        # Parse ISO dates
        try:
            ci = date.fromisoformat(check_in)
            co = date.fromisoformat(check_out)
        except ValueError:
            return json.dumps({"error": "ERR_PRICING_INVALID_DATE_FORMAT", "message": "I need exact, valid dates for this calculation."})
        
        # Calculate and validate length of stay
        nights = (co - ci).days
        if nights <= 0:
            return json.dumps({"error": "ERR_PRICING_INVALID_DATES", "message": "The check-out date must be after the check-in date."})
        
        if nights > 30:
            return json.dumps({"error": "ERR_PRICING_LOS_EXCEEDED", "message": "We currently do not support bookings longer than 30 nights online."})
        
        # Resolve path to the properties JSON data
        if data_path_str:
            properties_path = Path(data_path_str)
        else:
            settings = get_settings()
            properties_path = settings.properties_path
        
        # Read the properties data
        try:
            with open(properties_path, "r") as f:
                properties = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return json.dumps({"error": "ERR_PRICING_DATA_MISSING", "message": "Our pricing system is currently unavailable. Please try again later."})
        
        # Locate the property
        prop = next((p for p in properties if p.get("property_id") == property_id), None)
        if prop is None:
            return json.dumps({"error": "ERR_PRICING_PROPERTY_NOT_FOUND", "message": "I couldn't find that property in our system."})
        
        # Locate the room within the property
        room = next((r for r in prop.get("room_types", []) if r.get("room_id") == room_id), None)
        if room is None:
            return json.dumps({"error": "ERR_PRICING_ROOM_NOT_FOUND", "message": "I couldn't find that room type for the property."})
        
        try:
            # Base price calculation
            price_per_night = float(room.get("price_per_night", 0.0))
            base_price = round(nights * price_per_night, 2)
            
            # Map available add-ons for quick lookup
            available_addons = room.get("add_ons", [])
            addon_dict = {a.get("id"): a for a in available_addons}
            
            add_ons_breakdown = []
            add_ons_total = 0.0
            
            # Process requested add-ons
            if add_on_ids:
                for a_id in add_on_ids:
                    if a_id not in addon_dict:
                        return json.dumps({"error": "ERR_PRICING_INVALID_ADDON", "message": "One or more requested add-ons are not available for this room."})
                    addon = addon_dict[a_id]
                    addon_price = float(addon.get("price", 0.0))
                    
                    add_ons_breakdown.append({
                        "id": addon.get("id"),
                        "name": addon.get("name"),
                        "price": round(addon_price, 2)
                    })
                    add_ons_total += addon_price
            
            # Compute final totals, ensuring proper float rounding
            add_ons_total = round(add_ons_total, 2)
            total = round(base_price + add_ons_total, 2)
            per_night_rate = round(total / nights, 2)
            
            result = {
                "nights": nights,
                "base_price": base_price,
                "add_ons_breakdown": add_ons_breakdown,
                "add_ons_total": add_ons_total,
                "total": total,
                "per_night_rate": per_night_rate
            }
            if warnings:
                result["warnings"] = warnings
                
            return json.dumps(result)
            
        except (ValueError, TypeError, AttributeError, KeyError):
            return json.dumps({"error": "ERR_PRICING_DATA_CORRUPTED", "message": "Our pricing system encountered an error with the room rates."})

    except Exception:
        # Catch any other unexpected errors to prevent thread crash
        return json.dumps({"error": "ERR_PRICING_INTERNAL_ERROR", "message": "Our pricing system encountered an unexpected error."})
