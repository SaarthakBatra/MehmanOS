"""
AddOn and AddOnID schemas defining available hotel add-ons and their identifiers.
"""
from .components.add_on import AddOn, AddOnID

"""
Policies schema defining room-specific policies like check-in times and pet rules.
"""
from .components.policies import Policies

"""
Room schema defining the structure of a single hotel room type.
"""
from .components.room import Room

"""
Property schema and PropertiesDataset defining a full hotel property and the collection of properties.
"""
from .components.property import Property, PropertiesDataset

__all__ = [
    "AddOnID",
    "AddOn",
    "Policies",
    "Room",
    "Property",
    "PropertiesDataset",
]
