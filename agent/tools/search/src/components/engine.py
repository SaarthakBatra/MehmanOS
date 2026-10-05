"""
Engine Component for the Search Module.

Contains the core business logic and fallback tiers for executing property searches.
"""
import json
import logging
from pathlib import Path
from pydantic import ValidationError

from agent.config.src.config import get_settings
from .schemas import PropertySchema, SearchPropertiesRequest, SearchPropertiesResponse
from .tokenizer import _tokenize
from .matcher import _matches_preference
from .mapper import _map_to_search_result
from .sorter import _sort_results

logger = logging.getLogger(__name__)

def search_properties(
    destination: str | None = None,
    guests: int | None = None,
    budget_per_night: float | None = None,
    room_preference: str | None = None,
    **kwargs
) -> str:
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
    warnings_list = []
    data_path_str = kwargs.pop("_data_path", None)
    
    if kwargs:
        logger.warning(f"search_properties received hallucinated arguments: {kwargs}")
        warnings_list.append(f"Ignored unsupported arguments: {list(kwargs.keys())}")

    if data_path_str:
        properties_path = Path(data_path_str)
    else:
        settings = get_settings()
        properties_path = settings.properties_path

    if any(x is None for x in [destination, guests]):
        return json.dumps({
            "error": "ERR_SEARCH_MISSING_ARGS",
            "message": "Missing required search parameters. You must provide destination and guests."
        })

    str_args = [x for x in [destination, room_preference] if x is not None]
    if not all(isinstance(x, str) for x in str_args):
        return json.dumps({
            "error": "ERR_SEARCH_INVALID_ARGS",
            "message": "Invalid type. destination and room_preference must be strings."
        })
        
    num_args = [x for x in [guests, budget_per_night] if x is not None]
    if not all(isinstance(x, (int, float)) for x in num_args):
        return json.dumps({
            "error": "ERR_SEARCH_INVALID_ARGS",
            "message": "Invalid type. guests and budget_per_night must be numeric."
        })

    try:
        req = SearchPropertiesRequest(
            destination=destination,
            guests=guests,
            budget_per_night=budget_per_night,
            room_preference=room_preference
        )
    except ValidationError:
        return json.dumps({
            "error": "ERR_SEARCH_INVALID_ARGS",
            "message": "Invalid search parameter values."
        })

    try:
        with open(properties_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return json.dumps({
            "error": "ERR_SEARCH_DATA_MISSING",
            "message": "Failed to load properties dataset."
        })
    except json.JSONDecodeError:
        return json.dumps({
            "error": "ERR_SEARCH_JSON_PARSE_FAILED",
            "message": "Properties dataset contains malformed JSON syntax."
        })

    properties = []
    for p in data:
        try:
            properties.append(PropertySchema(**p))
        except ValidationError:
            return json.dumps({
                "error": "ERR_SEARCH_SCHEMA_INVALID",
                "message": "Properties dataset is structurally invalid."
            })

    # 1. Filter by destination
    matched_props = [
        p for p in properties 
        if req.destination.lower() in p.location.lower()
    ]

    if not matched_props:
        return json.dumps({
            "error": "ERR_SEARCH_DESTINATION_NOT_FOUND",
            "message": "No properties found in the requested destination."
        })

    tokens = _tokenize(req.room_preference)

    def get_matches(drop_pref: bool, drop_budget: bool, drop_capacity: bool):
        matches = []
        for p in matched_props:
            for r in p.room_types:
                if not drop_capacity and r.capacity < req.guests:
                    continue
                if drop_capacity and r.capacity >= req.guests:
                    continue # only return smaller rooms for drop_capacity fallback
                
                if not drop_budget and req.budget_per_night is not None and r.price_per_night > req.budget_per_night:
                    continue
                    
                if not drop_pref and not _matches_preference(r.name, r.amenities, tokens):
                    continue
                    
                matches.append(_map_to_search_result(p, r))
        return matches

    # Initial strict search
    results = get_matches(drop_pref=False, drop_budget=False, drop_capacity=False)
    if results:
        results = _sort_results(results, desc_capacity=False)
        return SearchPropertiesResponse(
            matches=results, 
            fallback=False,
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    # Fallback Tier 1: Drop preference, keep budget
    results = get_matches(drop_pref=True, drop_budget=False, drop_capacity=False)
    if results:
        results = _sort_results(results, desc_capacity=False)
        return SearchPropertiesResponse(
            matches=results, 
            fallback=True, 
            fallback_reason="No rooms matched the requested preference. Relaxed constraint.",
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    # Fallback Tier 2: Drop budget, keep preference
    results = get_matches(drop_pref=False, drop_budget=True, drop_capacity=False)
    if results:
        results = _sort_results(results, desc_capacity=False)
        return SearchPropertiesResponse(
            matches=results, 
            fallback=True, 
            fallback_reason="No rooms matched the requested budget. Relaxed constraint.",
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    # Fallback Tier 3: Drop both
    results = get_matches(drop_pref=True, drop_budget=True, drop_capacity=False)
    if results:
        results = _sort_results(results, desc_capacity=False)
        return SearchPropertiesResponse(
            matches=results, 
            fallback=True, 
            fallback_reason="No rooms matched preference or budget. Relaxed both constraints.",
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    # Fallback Tier 4: Drop capacity (keep destination only)
    results = []
    for p in matched_props:
        for r in p.room_types:
            if r.capacity < req.guests:
                results.append(_map_to_search_result(p, r))
    if results:
        results = _sort_results(results, desc_capacity=True)
        return SearchPropertiesResponse(
            matches=results, 
            fallback=True, 
            fallback_reason=f"No single room accommodates {req.guests} guests. Suggest booking multiple rooms.",
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    # If all fallbacks fail (should be rare if there are ANY rooms in the destination)
    return json.dumps({
        "error": "ERR_SEARCH_NO_ROOMS_AT_ALL",
        "message": "No rooms available in the requested destination."
    })
