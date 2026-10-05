"""
Main parser component for the date_parser module.
Handles validation, normalization, rejection logic, and orchestration of the single parser.
"""

import datetime
import logging
import re

from .models import ParsedDates
from .single_parser import _parse_single


def parse_date_string(
    raw_input: str,
    reference_date: datetime.date,
    timezone: str = 'Asia/Kolkata',
    languages: list[str] | None = None
) -> ParsedDates:
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
    languages = languages or ['en']

    # Validate that reference_date is strictly a date, not a datetime
    if not isinstance(reference_date, datetime.date) or isinstance(reference_date, datetime.datetime):
        raise TypeError("reference_date must be a naive datetime.date object")

    if not isinstance(raw_input, str) or not raw_input.strip():
        logging.warning("date_parser rejected input: empty or invalid type")
        return ParsedDates(start_date=None, end_date=None)

    raw_input = raw_input.strip()
    raw_input_lower = raw_input.lower()

    # Normalization: strip trailing punctuation to prevent parser confusion
    raw_input = re.sub(r'[!.,;?]+$', '', raw_input)
    raw_input_lower = re.sub(r'[!.,;?]+$', '', raw_input_lower)

    # Reject unsupported holidays
    holidays = ["christmas", "new year", "thanksgiving", "halloween", "valentine"]
    if any(h in raw_input_lower for h in holidays):
        logging.warning("date_parser rejected input: Named holiday detected.")
        return ParsedDates(start_date=None, end_date=None)

    # Reject inputs containing conjunctions to enforce single-intent parsing
    if re.search(r'\b(and|&)\b', raw_input_lower):
        logging.warning(f"date_parser rejected input: Conjunction detected in '{raw_input}'")
        return ParsedDates(start_date=None, end_date=None)

    # Reject vague colloquialisms that don't map to concrete dates
    vague_phrases = ["next week", "next month", "a couple of days", "end of the week", "mid-month", "sometime later"]
    if raw_input_lower in vague_phrases:
        logging.warning("date_parser rejected input: Ambiguous period or vague offset.")
        return ParsedDates(start_date=None, end_date=None)

    # Reject durations provided without a relative anchor (e.g., "3 days")
    duration_match = re.fullmatch(r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|a)\s+(days?|weeks?|months?|years?)', raw_input_lower)
    if duration_match:
        logging.warning("date_parser rejected input: Standalone duration.")
        return ParsedDates(start_date=None, end_date=None)

    # Reject purely time-based inputs unless they contain a day reference like "tonight"
    time_match = re.fullmatch(r'[\d\:\s]*(am|pm|morning|evening|night|afternoon|tonight)', raw_input_lower)
    if time_match and "tonight" not in raw_input_lower:
        logging.warning("date_parser rejected input: Pure time string.")
        return ParsedDates(start_date=None, end_date=None)
    
    if re.fullmatch(r'\d{1,2}:\d{2}', raw_input_lower):
        logging.warning("date_parser rejected input: Pure time string.")
        return ParsedDates(start_date=None, end_date=None)

    # Attempt to split ranges formatted like "Monday to Friday" or "Oct 1 - Oct 5"
    range_parts = re.split(r'\s+to\s+|\s*-\s*', raw_input, flags=re.IGNORECASE)
    if len(range_parts) == 2:
        start_pd = _parse_single(range_parts[0], reference_date, timezone, languages)
        end_pd = _parse_single(range_parts[1], reference_date, timezone, languages)
        if start_pd and end_pd:
            return ParsedDates(start_date=start_pd, end_date=end_pd)
        # Try to parse both sides; if either fails, reject the entire range.
        return ParsedDates(start_date=None, end_date=None)

    # Process as a single date
    single = _parse_single(raw_input, reference_date, timezone, languages)
    if single:
        return ParsedDates(start_date=single, end_date=single)
    
    return ParsedDates(start_date=None, end_date=None)
