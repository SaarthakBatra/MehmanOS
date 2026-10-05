"""
Router for the booking module.
Exposes booking operations from individual component files.
"""
from .components import creator, admin, retriever, canceller

"""
Create a temporary booking hold for a specific property and room.

Validates inputs, ensures availability, calculates the total price,
and inserts a new booking record into the database with a 'hold' status.

Args:
    property_id (str): The unique identifier for the property.
    room_id (str): The unique identifier for the room type.
    check_in (str): Check-in date in YYYY-MM-DD format.
    check_out (str): Check-out date in YYYY-MM-DD format.
    guests (int): Number of guests for the booking.
    guest_name (str): The primary guest's full name.
    guest_phone (str): The primary guest's contact phone number.
    add_on_ids (list[str] | None): Optional list of add-on identifiers.
    **kwargs: Injected dependencies for testing and system context
        (_data_path, _db_path, _system_date, _check_availability_func,
        _calculate_price_func, _uuid_func).

Returns:
    str: A JSON-encoded string containing either the booking hold details
         or an error payload with an error code and message.
"""
def create_booking_hold(
    property_id: str = None,
    room_id: str = None,
    check_in: str = None,
    check_out: str = None,
    guests: int = None,
    guest_name: str = None,
    guest_phone: str = None,
    add_on_ids: list[str] | None = None,
    **kwargs
) -> str:
    return creator.create_booking_hold(
        property_id=property_id,
        room_id=room_id,
        check_in=check_in,
        check_out=check_out,
        guests=guests,
        guest_name=guest_name,
        guest_phone=guest_phone,
        add_on_ids=add_on_ids,
        **kwargs
    )

"""
Clear all records from the bookings table for administrative or testing purposes.

Args:
    _db_path (str, optional): An injected database path for testing overrides.

Returns:
    bool: True if the database reset was successful, False otherwise.
"""
def admin_reset_database(_db_path: str = None) -> bool:
    return admin.admin_reset_database(_db_path=_db_path)

"""
Retrieve existing bookings by phone number or booking reference.

Args:
    lookup_value (str): The phone number or booking reference to search for.
    lookup_type (str): The type of lookup ('phone' or 'ref'). Defaults to 'phone'.
    **kwargs: Injected dependencies for testing and system context (_db_path).

Returns:
    str: A JSON-encoded string containing a list of booking details or an error payload.
"""
def get_booking(lookup_value: str = None, lookup_type: str = 'phone', **kwargs) -> str:
    return retriever.get_booking(lookup_value=lookup_value, lookup_type=lookup_type, **kwargs)

"""
Cancel an existing booking.

Args:
    booking_ref (str): The unique booking reference to cancel.
    **kwargs: Injected dependencies for testing and system context (_db_path).

Returns:
    str: A JSON-encoded string containing the result of the cancellation or an error payload.
"""
def cancel_booking(booking_ref: str = None, **kwargs) -> str:
    return canceller.cancel_booking(booking_ref=booking_ref, **kwargs)
