"""
Router for the details module.
"""
from agent.tools.details.src.components.property_details import get_property_details as _get_property_details
from agent.tools.details.src.components.room_details import get_room_details as _get_room_details

"""
Retrieve details for a specific property.

Args:
    property_id (str): The unique identifier for the property.
    **kwargs: Optional keyword arguments, such as _data_path for testing.

Returns:
    str: A JSON-encoded string containing the property details or an error message.
"""
def get_property_details(property_id: str = None, **kwargs) -> str:
    return _get_property_details(property_id=property_id, **kwargs)

"""
Retrieve details for a specific room within a property.

Args:
    property_id (str): The unique identifier for the property.
    room_id (str): The unique identifier for the room.
    **kwargs: Optional keyword arguments, such as _data_path for testing.

Returns:
    str: A JSON-encoded string containing the room details or an error message.
"""
def get_room_details(property_id: str = None, room_id: str = None, **kwargs) -> str:
    return _get_room_details(property_id=property_id, room_id=room_id, **kwargs)
