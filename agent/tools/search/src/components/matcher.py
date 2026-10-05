"""
Matcher Component for the Search Module.

Provides the logic to match search tokens against a room's name and amenities.
"""
import re

def _matches_preference(room_name: str, amenities: list[str], tokens: list[str]) -> bool:
    """
    Checks if a room matches the specified preference tokens using word-boundary matching.

    The function checks both the room's amenities and its name for any exact match
    with the provided tokens.

    Args:
        room_name (str): The name of the room.
        amenities (list[str]): A list of amenities available in the room.
        tokens (list[str]): A list of search tokens (e.g., preference keywords).

    Returns:
        bool: True if at least one token is found in the room name or amenities, False otherwise.
    """
    if not tokens:
        return True
    
    # Check if any token matches an amenity exactly (word-boundary)
    for amenity in amenities:
        amenity_lower = amenity.lower()
        for token in tokens:
            if re.search(rf'\b{re.escape(token)}\b', amenity_lower):
                return True
                
    # Check if any token matches the room name exactly
    room_name_lower = room_name.lower()
    for token in tokens:
        if re.search(rf'\b{re.escape(token)}\b', room_name_lower):
            return True
            
    return False
