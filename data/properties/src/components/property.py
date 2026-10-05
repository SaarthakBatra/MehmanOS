from pydantic import BaseModel, Field, ConfigDict
from .room import Room

class Property(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Pattern ensures property ID matches GOA followed by exactly 3 digits.
    property_id: str = Field(..., pattern=r"^GOA\d{3}$", description="Unique ID for the property (e.g. GOA001)")
    name: str = Field(..., description="Name of the property")
    location: str = Field(..., description="Location of the property")
    description: str = Field(..., description="Description of the property")
    # Rating must be between 0.0 and 5.0 inclusive.
    rating: float = Field(..., ge=0, le=5.0, description="Star rating of the property")
    room_types: list[Room] = Field(..., description="List of available rooms in the property")

PropertiesDataset = list[Property]
