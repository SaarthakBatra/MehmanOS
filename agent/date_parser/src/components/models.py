"""
Models component for the date_parser module.
Contains dataclasses and constants used across parsing logic.
"""

import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedDates:
    """
    Represents the start and end dates parsed from a raw input string.

    Attributes:
        start_date (Optional[datetime.date]): The starting date of the parsed period, or None if unparseable.
        end_date (Optional[datetime.date]): The ending date of the parsed period, or None if unparseable.
    """
    start_date: datetime.date | None
    end_date: datetime.date | None


# Integer mapping aligns with Python's datetime.weekday() (0=Monday, 6=Sunday)
WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6
}
