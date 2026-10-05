"""
Mapper Component for the Search Module.

Provides functionality to map property and room data schemas to search result objects.
"""
from .schemas import PropertySchema, RoomSchema, SearchResultRoom

def _map_to_search_result(prop: PropertySchema, room: RoomSchema) -> SearchResultRoom:
    """
    Maps PropertySchema and RoomSchema instances into a combined SearchResultRoom response object.

    Args:
        prop (PropertySchema): The property model.
        room (RoomSchema): The room model.

    Returns:
        SearchResultRoom: A response schema containing combined room and property details.
    """
    return SearchResultRoom(
        property_id=prop.property_id,
        property_name=prop.name,
        location=prop.location,
        room_id=room.room_id,
        room_name=room.name,
        capacity=room.capacity,
        price_per_night=room.price_per_night,
        amenities=room.amenities
    )
