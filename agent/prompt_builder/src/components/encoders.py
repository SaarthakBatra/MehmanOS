"""
Provides JSON encoding utilities for date and datetime objects.
"""
import datetime

def _date_encoder(obj):
    """
    JSON encoder function for serializing datetime objects.
    
    Args:
        obj: The object to serialize.
        
    Returns:
        str: The ISO 8601 string representation if the object is a datetime or date.
        
    Raises:
        TypeError: If the object is not a supported datetime type.
    """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        # Ensure standard ISO 8601 string formatting for all temporal objects
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
