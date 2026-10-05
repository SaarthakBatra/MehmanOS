"""
Router for the Search Module.

Exposes the public API for the search tool while delegating implementation to components.
"""
from .components.engine import search_properties as core_search_properties

"""
Searches for available properties and rooms matching the given criteria.
Implements a 4-tier fallback cascade if strict constraints cannot be met.

Args:
    destination (str | None): The location to search in.
    guests (int | None): The number of guests to accommodate.
    budget_per_night (float | None): The maximum budget per night.
    room_preference (str | None): Keywords for preferred room features or amenities.
    **kwargs: Extraneous arguments (used to detect hallucinations and inject paths).

Returns:
    str: A JSON-serialized response containing matching rooms, fallback status, and any errors/warnings.
"""
def search_properties(
    destination: str | None = None,
    guests: int | None = None,
    budget_per_night: float | None = None,
    room_preference: str | None = None,
    **kwargs
) -> str:
    return core_search_properties(
        destination=destination, 
        guests=guests, 
        budget_per_night=budget_per_night, 
        room_preference=room_preference, 
        **kwargs
    )
