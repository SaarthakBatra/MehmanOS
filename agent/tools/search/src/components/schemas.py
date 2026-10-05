"""
Pydantic Schemas for the Search Module.

Provides the data structures for properties, rooms, search requests, and search results.
"""
from typing import Any
from pydantic import BaseModel, Field

class RoomSchema(BaseModel):
    """Schema representing an individual room type within a property."""
    room_id: str
    name: str
    capacity: int
    price_per_night: float
    amenities: list[str]
    policies: dict[str, str]
    add_ons: list[dict[str, Any]]

class PropertySchema(BaseModel):
    """Schema representing a property and its available room types."""
    property_id: str
    name: str
    location: str
    description: str
    rating: float
    room_types: list[RoomSchema]

class SearchPropertiesRequest(BaseModel):
    """Schema for validating incoming search requests."""
    destination: str
    guests: int = Field(..., ge=1)
    budget_per_night: float | None = Field(None, ge=0)
    room_preference: str | None = None

class SearchResultRoom(BaseModel):
    """Schema for an individual matched room in the search results."""
    property_id: str
    property_name: str
    location: str
    room_id: str
    room_name: str
    capacity: int
    price_per_night: float
    amenities: list[str]

class SearchPropertiesResponse(BaseModel):
    """Schema for the final search response payload."""
    matches: list[SearchResultRoom]
    fallback: bool
    fallback_reason: str | None = None
    warnings: list[str] | None = None
