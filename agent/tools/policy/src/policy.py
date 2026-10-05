import json
import logging
from pathlib import Path

from pydantic import BaseModel

from agent.config.src.config import get_settings

logger = logging.getLogger(__name__)

class PolicySuccessResponse(BaseModel):
    """Schema for a successful policy retrieval response."""
    result: str | dict[str, str]
    warnings: list[str] | None = None

class PolicyErrorResponse(BaseModel):
    """Schema for an error response when policy retrieval fails."""
    error: str
    message: str

ALLOWED_POLICIES = {"cancellation", "pet_policy", "child_policy", "check_in", "check_out", "all"}

def get_policy(
    property_id: str | None = None,
    room_id: str | None = None,
    policy_type: str | None = None,
    **kwargs
) -> str:
    """
    Retrieves specific hotel policies (cancellation, pets, children, check-in/out) 
    for a specific room. Use 'all' to get all policies. Do not guess policies. 
    If the policy is not found, apologize and inform the guest.
    
    Args:
        property_id (str | None): The ID of the property. Must be uppercase, e.g., 'GOA001'.
        room_id (str | None): The ID of the room. Must be uppercase, e.g., 'GOA001-DELUXE'.
        policy_type (str | None): The type of policy to retrieve. Must be one of:
            'cancellation', 'pet_policy', 'child_policy', 'check_in', 'check_out', or 'all'.
        **kwargs: Absorbs any extra hallucinated parameters from the LLM.
                     
    Returns:
        str: A JSON string containing either the specific policy string, 
             a dictionary of all policies (if 'all' is requested), 
             or an error dictionary if the property/room/policy is not found.
    """
    try:
        # Determine the dataset path, allowing for test injection via kwargs
        data_path_str = kwargs.pop("_data_path", None)
        if data_path_str:
            properties_path = Path(data_path_str)
        else:
            settings = get_settings()
            properties_path = settings.properties_path

        # Handle hallucinated arguments silently and store warnings
        warnings_list = []
        if kwargs:
            logger.warning("Hallucinated parameters ignored", extra={"kwargs": kwargs})
            warnings_list.append(f"Ignored unexpected arguments: {list(kwargs.keys())}")

        # 1. Missing/Null Argument Validation
        if any(x is None for x in [property_id, room_id, policy_type]):
            return PolicyErrorResponse(
                error="MISSING_ARGUMENT",
                message="Missing required arguments. You must provide property_id, room_id, and policy_type."
            ).model_dump_json(exclude_none=True)

        # 2. Argument Type Validation
        if not all(isinstance(x, str) for x in [property_id, room_id, policy_type]):
            return PolicyErrorResponse(
                error="INVALID_ARGUMENT_TYPE",
                message="Invalid type. property_id, room_id and policy_type must be strings."
            ).model_dump_json(exclude_none=True)

        # Clean and normalize strings in place for reliable comparisons
        property_id = property_id.strip().upper()
        room_id = room_id.strip().upper()
        policy_type = policy_type.strip().lower()

        # 3. Enum Validation
        if policy_type not in ALLOWED_POLICIES:
            return PolicyErrorResponse(
                error="INVALID_POLICY_TYPE",
                message=f"Invalid policy type '{policy_type}'. Allowed values are: cancellation, pet_policy, child_policy, check_in, check_out, all."
            ).model_dump_json(exclude_none=True)

        # Load the properties dataset
        try:
            with open(properties_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return PolicyErrorResponse(
                error="INTERNAL_SYSTEM_ERROR",
                message=f"An unexpected system error occurred: {str(e)}"
            ).model_dump_json(exclude_none=True)

        # 4. Property Data Lookup
        prop = next((p for p in data if p.get("property_id") == property_id), None)
        if not prop:
            return PolicyErrorResponse(
                error="PROPERTY_NOT_FOUND",
                message=f"Property '{property_id}' not found in dataset."
            ).model_dump_json(exclude_none=True)

        # 5. Room Data Lookup
        room = next((r for r in prop.get("room_types", []) if r.get("room_id") == room_id), None)
        if not room:
            return PolicyErrorResponse(
                error="ROOM_NOT_FOUND",
                message=f"Room '{room_id}' not found in property '{property_id}'."
            ).model_dump_json(exclude_none=True)

        # 6. Policy Key Lookup
        policies = room.get("policies")
        if policies is None or not isinstance(policies, dict):
            return PolicyErrorResponse(
                error="POLICY_NOT_FOUND",
                message=f"Policy '{policy_type}' not specified for room '{room_id}' in property '{property_id}'."
            ).model_dump_json(exclude_none=True)

        # Return all policies if explicitly requested
        if policy_type == "all":
            return PolicySuccessResponse(
                result=policies,
                warnings=warnings_list if warnings_list else None
            ).model_dump_json(exclude_none=True)

        # Retrieve specific policy and check for empty strings
        policy_val = policies.get(policy_type, "")
        if not policy_val:
            return PolicyErrorResponse(
                error="POLICY_NOT_FOUND",
                message=f"Policy '{policy_type}' not specified for room '{room_id}' in property '{property_id}'."
            ).model_dump_json(exclude_none=True)

        return PolicySuccessResponse(
            result=policy_val,
            warnings=warnings_list if warnings_list else None
        ).model_dump_json(exclude_none=True)

    except Exception as e:
        # Catch-all safety net for unexpected runtime errors
        return PolicyErrorResponse(
            error="INTERNAL_SYSTEM_ERROR",
            message=f"An unexpected system error occurred: {str(e)}"
        ).model_dump_json(exclude_none=True)
