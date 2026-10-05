from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

class AddOnID(str, Enum):
    BREAKFAST = "BREAKFAST"
    AIRPORT_PICKUP = "AIRPORT_PICKUP"
    LATE_CHECKOUT = "LATE_CHECKOUT"
    BICYCLE_RENTAL = "BICYCLE_RENTAL"
    SPA_VOUCHER = "SPA_VOUCHER"
    PRIVATE_CHEF = "PRIVATE_CHEF"
    DECORATION = "DECORATION"

class AddOn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: AddOnID = Field(..., description="Unique identifier for the add-on")
    name: str = Field(..., description="Human readable name of the add-on")
    # Must be non-negative as prices cannot be negative.
    price: float = Field(..., ge=0, description="Price of the add-on in INR")
