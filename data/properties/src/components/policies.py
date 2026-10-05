import datetime
from pydantic import BaseModel, Field, ConfigDict

class Policies(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cancellation: str = Field(..., description="Cancellation policy text")
    pet_policy: str = Field(..., description="Pet policy text")
    child_policy: str = Field(..., description="Child policy text")
    # Pydantic natively validates datetime.time formats (e.g., "14:00").
    check_in: datetime.time = Field(..., description="Check-in time (e.g., 14:00)")
    check_out: datetime.time = Field(..., description="Check-out time (e.g., 11:00)")
