"""
Sorter Component for the Search Module.

Provides functionality to sort search results based on capacity, price, and ID.
"""
from .schemas import SearchResultRoom

def _sort_results(results: list[SearchResultRoom], desc_capacity: bool = False) -> list[SearchResultRoom]:
    """
    Sorts search results by capacity (ascending or descending), price per night, and room ID.

    Args:
        results (list[SearchResultRoom]): The list of search results to sort.
        desc_capacity (bool): If True, sorts capacity in descending order (useful when suggesting multiple rooms).

    Returns:
        list[SearchResultRoom]: The sorted list of search results.
    """
    return sorted(
        results,
        key=lambda r: (-r.capacity if desc_capacity else r.capacity, r.price_per_night, r.room_id)
    )
