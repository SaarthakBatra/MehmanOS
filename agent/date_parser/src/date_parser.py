"""
Router for the date_parser module.
Exposes the public interface for date parsing.
"""

import datetime

from .components.models import ParsedDates, WEEKDAYS
from .components.main_parser import parse_date_string as _parse_date_string_impl

"""
Parses a natural language date string into a structured start and end date.

Args:
    raw_input (str): The raw string to parse.
    reference_date (datetime.date): The base date used to resolve relative offsets (e.g., 'tomorrow').
    timezone (str): The timezone used during parsing (default: 'Asia/Kolkata').
    languages (Optional[list[str]]): A list of language codes to support (default: ['en']).

Returns:
    ParsedDates: A dataclass containing the resolved start_date and end_date. 
                 Returns (None, None) if the input is invalid or cannot be parsed.

Raises:
    TypeError: If reference_date is not a naive datetime.date object.
"""
def parse_date_string(
    raw_input: str,
    reference_date: datetime.date,
    timezone: str = 'Asia/Kolkata',
    languages: list[str] | None = None
) -> ParsedDates:
    return _parse_date_string_impl(raw_input, reference_date, timezone, languages)
