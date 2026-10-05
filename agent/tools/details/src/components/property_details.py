"""
Component providing the get_property_details function.
This function retrieves details for a specific property.
"""
import json
from pathlib import Path

from agent.config.src.config import get_settings

def get_property_details(property_id: str = None, **kwargs) -> str:
    """
    Retrieve details for a specific property.

    Args:
        property_id (str): The unique identifier for the property.
        **kwargs: Optional keyword arguments, such as _data_path for testing.

    Returns:
        str: A JSON-encoded string containing the property details or an error message.
    """
    try:
        # Guard clause for missing required arguments
        if property_id is None:
            err = {"error": "ERR_DETAILS_MISSING_ARGS", "message": "property_id is required"}
            return json.dumps(err)

        # Guard clause for invalid argument types
        if not isinstance(property_id, str):
            err = {"error": "INVALID_ARGUMENT_TYPE", "message": "Invalid type. property_id must be a string."}
            return json.dumps(err)

        property_id = property_id.upper()

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
            
        return json.dumps(target_property)
    except Exception as e:
        return json.dumps({"error": "INTERNAL_SYSTEM_ERROR", "message": str(e)})
