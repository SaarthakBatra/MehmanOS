from pydantic import BaseModel, Field, ConfigDict
from .policies import Policies
from .add_on import AddOn

class Room(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Pattern ensures room ID matches GOA followed by 3 digits, a hyphen, and uppercase letters.
    room_id: str = Field(..., pattern=r"^GOA\d{3}-[A-Z]+$", description="Unique ID for the room (e.g. GOA001-DELUXE)")
    name: str = Field(..., description="Name of the room")
    capacity: int = Field(..., ge=1, description="Maximum number of guests allowed")
    price_per_night: float = Field(..., ge=0, description="Price per night in INR")
    amenities: list[str] = Field(..., description="List of included amenities")
    policies: Policies = Field(..., description="Room specific policies")
    add_ons: list[AddOn] = Field(..., description="Available add-ons for this room")
