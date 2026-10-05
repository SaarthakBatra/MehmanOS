"""
Handles the execution of dynamically loaded tools and their schemas.
"""
import sys
import logging
from google.genai.types import FunctionDeclaration, Type, Schema

logger = logging.getLogger(__name__)

# Import tool implementations dynamically to avoid circular dependencies
try:
    from agent.tools.search.src.search import search_properties
except ImportError:
    search_properties = None

try:
    from agent.tools.availability.src.availability import check_availability
except ImportError:
    check_availability = None

try:
    from agent.tools.details.src.details import get_room_details, get_property_details
except ImportError:
    get_room_details = None
    get_property_details = None

try:
    from agent.tools.pricing.src.pricing import calculate_price
except ImportError:
    calculate_price = None

try:
    from agent.tools.policy.src.policy import get_policy
except ImportError:
    get_policy = None

try:
    from agent.tools.booking.src.booking import create_booking_hold, get_booking, cancel_booking
except ImportError:
    create_booking_hold = None
    get_booking = None
    cancel_booking = None


TOOL_SCHEMAS = [
    FunctionDeclaration(
        name="search_properties",
        description="Search for properties based on destination and dates.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "destination": Schema(type=Type.STRING),
                "guests": Schema(type=Type.INTEGER),
                "budget_per_night": Schema(type=Type.NUMBER),
                "room_preference": Schema(type=Type.STRING)
            },
            required=["destination", "guests"]
        )
    ),
    FunctionDeclaration(
        name="check_availability",
        description="Check if a room is available.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING),
                "room_id": Schema(type=Type.STRING),
                "check_in": Schema(type=Type.STRING),
                "check_out": Schema(type=Type.STRING)
            },
            required=["property_id", "room_id", "check_in", "check_out"]
        )
    ),
    FunctionDeclaration(
        name="calculate_price",
        description="Calculate the total price for a stay.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING),
                "room_id": Schema(type=Type.STRING),
                "check_in": Schema(type=Type.STRING),
                "check_out": Schema(type=Type.STRING),
                "add_on_ids": Schema(type=Type.ARRAY, items=Schema(type=Type.STRING))
            },
            required=["property_id", "room_id", "check_in", "check_out"]
        )
    ),
    FunctionDeclaration(
        name="get_room_details",
        description="Get amenities and details for a room.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING),
                "room_id": Schema(type=Type.STRING)
            },
            required=["property_id", "room_id"]
        )
    ),
    FunctionDeclaration(
        name="get_property_details",
        description="Get all rooms and property-level details for a property.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING)
            },
            required=["property_id"]
        )
    ),
    FunctionDeclaration(
        name="get_policy",
        description="Get policies for a property.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING),
                "room_id": Schema(type=Type.STRING),
                "policy_type": Schema(type=Type.STRING)
            },
            required=["property_id", "room_id", "policy_type"]
        )
    ),
    FunctionDeclaration(
        name="create_booking_hold",
        description="Create a temporary hold for a booking.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "property_id": Schema(type=Type.STRING),
                "room_id": Schema(type=Type.STRING),
                "check_in": Schema(type=Type.STRING),
                "check_out": Schema(type=Type.STRING),
                "guests": Schema(type=Type.INTEGER),
                "guest_name": Schema(type=Type.STRING),
                "guest_phone": Schema(type=Type.STRING),
                "add_on_ids": Schema(type=Type.ARRAY, items=Schema(type=Type.STRING))
            },
            required=["property_id", "room_id", "check_in", "check_out", "guests", "guest_name", "guest_phone"]
        )
    ),
    FunctionDeclaration(
        name="get_booking",
        description="Retrieve details about a guest's existing booking.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "lookup_value": Schema(type=Type.STRING),
                "lookup_type": Schema(type=Type.STRING)
            },
            required=["lookup_value", "lookup_type"]
        )
    ),
    FunctionDeclaration(
        name="cancel_booking",
        description="Cancel a guest's existing booking hold.",
        parameters=Schema(
            type=Type.OBJECT,
            properties={
                "booking_ref": Schema(type=Type.STRING)
            },
            required=["booking_ref"]
        )
    )
]


def _run_tool(name: str, kwargs: dict) -> dict:
    """
    Executes a booking tool by name, dynamically resolving the implementation.

    Args:
        name (str): The name of the tool to execute.
        kwargs (dict): The arguments to pass to the tool.

    Returns:
        dict: The result of the tool execution.

    Raises:
        ValueError: If the requested tool is not found.
    """
    # Dynamically check sys.modules to prioritize mocked versions in test environments
    if name == "search_properties":
        if 'agent.tools.search' in sys.modules and hasattr(sys.modules['agent.tools.search'], 'search_properties'):
            return sys.modules['agent.tools.search'].search_properties(**kwargs)
        elif search_properties:
            return search_properties(**kwargs)
            
    elif name == "check_availability":
        if 'agent.tools.availability' in sys.modules and hasattr(sys.modules['agent.tools.availability'], 'check_availability'):
            return sys.modules['agent.tools.availability'].check_availability(**kwargs)
        elif check_availability:
            return check_availability(**kwargs)
            
    elif name == "calculate_price" and calculate_price:
        if 'agent.tools.pricing' in sys.modules and hasattr(sys.modules['agent.tools.pricing'], 'calculate_price'):
            return sys.modules['agent.tools.pricing'].calculate_price(**kwargs)
        return calculate_price(**kwargs)
        
    elif name == "get_room_details" and get_room_details:
        return get_room_details(**kwargs)
        
    elif name == "get_property_details" and get_property_details:
        return get_property_details(**kwargs)
        
    elif name == "get_policy" and get_policy:
        return get_policy(**kwargs)
        
    elif name == "create_booking_hold" and create_booking_hold:
        # Inject required internal dependencies for booking creation
        kwargs["_check_availability_func"] = check_availability
        kwargs["_calculate_price_func"] = calculate_price
        
        if 'agent.tools.booking' in sys.modules and hasattr(sys.modules['agent.tools.booking'], 'create_booking_hold'):
            return sys.modules['agent.tools.booking'].create_booking_hold(**kwargs)
        return create_booking_hold(**kwargs)
        
    elif name == "get_booking" and get_booking:
        if 'agent.tools.booking' in sys.modules and hasattr(sys.modules['agent.tools.booking'], 'get_booking'):
            return sys.modules['agent.tools.booking'].get_booking(**kwargs)
        return get_booking(**kwargs)
        
    elif name == "cancel_booking" and cancel_booking:
        if 'agent.tools.booking' in sys.modules and hasattr(sys.modules['agent.tools.booking'], 'cancel_booking'):
            return sys.modules['agent.tools.booking'].cancel_booking(**kwargs)
        return cancel_booking(**kwargs)
        
    elif name == "search":
        # Legacy/fallback behavior check
        if 'agent.tools.search' in sys.modules and hasattr(sys.modules['agent.tools.search'], 'search'):
            return sys.modules['agent.tools.search'].search(**kwargs)
        raise ValueError(
            f"Tool '{name}' not found. Available tools: search_properties, get_room_details, "
            "check_availability, calculate_price, get_policy, create_booking_hold, get_booking, cancel_booking"
        )
        
    else:
        raise ValueError(
            f"Tool '{name}' not found. Available tools: search_properties, get_room_details, "
            "get_property_details, check_availability, calculate_price, get_policy, "
            "create_booking_hold, get_booking, cancel_booking"
        )
