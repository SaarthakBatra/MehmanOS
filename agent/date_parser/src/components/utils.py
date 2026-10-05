"""
Utilities component for the date_parser module.
Contains helper functions for date calculations.
"""

import datetime


def _get_weekday_offset(ref_date: datetime.date, target_weekday_idx: int) -> int:
    """
    Calculates the number of days until the next occurrence of a target weekday.

    Args:
        ref_date (datetime.date): The base date to calculate from.
        target_weekday_idx (int): The integer index of the target weekday (0=Monday, 6=Sunday).

    Returns:
        int: The number of days remaining.
    """
    days_ahead = target_weekday_idx - ref_date.weekday()
    # If the target weekday has already passed this week, wrap around to next week
    if days_ahead < 0:
        days_ahead += 7
    return days_ahead
