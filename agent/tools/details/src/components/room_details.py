"""
Component providing the get_room_details function.
This function retrieves details for a specific room within a property.
"""
import json
import logging
from pathlib import Path

from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

def get_room_details(property_id: str = None, room_id: str = None, **kwargs) -> str:
    """
    Retrieve details for a specific room within a property.

    Args:
        property_id (str): The unique identifier for the property.
        room_id (str): The unique identifier for the room.
        **kwargs: Optional keyword arguments, such as _data_path for testing.

    Returns:
        str: A JSON-encoded string containing the room details or an error message.
    """
    try:
        # Guard clause for missing required arguments
        if any(x is None for x in [property_id, room_id]):
            err = {"error": "ERR_DETAILS_MISSING_ARGS", "message": "property_id and room_id are required"}
            return json.dumps(err)

        # Guard clause for invalid argument types
        if not all(isinstance(x, str) for x in [property_id, room_id]):
            err = {"error": "INVALID_ARGUMENT_TYPE", "message": "Invalid type. property_id and room_id must be strings."}
            return json.dumps(err)

        # Handle unexpected kwargs for LLM self-correction
        unexpected_kwargs = [k for k in kwargs if k != '_data_path']
        warning_msg = None
        if unexpected_kwargs:
            logger.warning(f"get_room_details received unexpected kwargs: {unexpected_kwargs}")
            warning_msg = f"Unsupported arguments ignored: {unexpected_kwargs}"

        property_id = property_id.upper()
        room_id = room_id.upper()

        # Determine dataset path, allowing overrides for testing
        data_path_str = kwargs.get("_data_path")
        if data_path_str:
            properties_path = Path(data_path_str)
        else:
            settings = get_settings()
            properties_path = settings.properties_path
        
        # Verify dataset existence
        if not properties_path.is_file():
            err = {"error": "ERR_DETAILS_DATASET_MISSING", "message": "Dataset file missing or unreadable"}
            return json.dumps(err)
        
        # Load dataset
        try:
            with open(properties_path, "r", encoding="utf-8") as f:
                properties = json.load(f)
        except Exception:
            err = {"error": "ERR_DETAILS_INVALID_JSON", "message": "Dataset file contains malformed JSON"}
            return json.dumps(err)
        
        if not isinstance(properties, list):
            properties = []
            
        # Locate the requested property
        target_property = next((p for p in properties if isinstance(p, dict) and str(p.get("property_id", "")).upper() == property_id), None)
        
        if not target_property:
            err = {"error": "ERR_DETAILS_PROPERTY_NOT_FOUND", "message": f"Property '{property_id}' not found in dataset"}
            return json.dumps(err)
            
        room_types = target_property.get("room_types", [])
        if not isinstance(room_types, list):
            room_types = []
            
        # Locate the requested room
        target_room = next((r for r in room_types if isinstance(r, dict) and str(r.get("room_id", "")).upper() == room_id), None)
        
        if not target_room:
            err = {"error": "ERR_DETAILS_ROOM_NOT_FOUND", "message": f"Room '{room_id}' not found within property '{property_id}'"}
            return json.dumps(err)
            
        # Inject warnings if unexpected kwargs were passed
        if warning_msg:
            target_room["warnings"] = [warning_msg]
            
        return json.dumps(target_room)
    except Exception as e:
        return json.dumps({"error": "INTERNAL_SYSTEM_ERROR", "message": str(e)})
