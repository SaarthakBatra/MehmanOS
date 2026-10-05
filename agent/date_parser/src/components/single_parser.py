"""
Single date parser component for the date_parser module.
Handles logic for parsing single date formats and relative date words.
"""

import datetime
import logging
import re
import dateparser

from .models import WEEKDAYS
from .utils import _get_weekday_offset


def _parse_single(text: str, ref_date: datetime.date, tz: str, langs: list[str]) -> datetime.date | None:
    """
    Parses a single (non-range) date string.

    Args:
        text (str): The specific text to parse.
        ref_date (datetime.date): The base date for relative offsets.
        tz (str): The timezone configuration.
        langs (list[str]): The supported language codes.

    Returns:
        datetime.date | None: The resolved date, or None if parsing fails.
    """
    text_lower = text.lower()

    # Fast-path for exact phrase matches
    if text_lower == "day after tomorrow":
        return ref_date + datetime.timedelta(days=2)
    if text_lower == "a week from today":
        return ref_date + datetime.timedelta(days=7)
    if text_lower == "tonight":
        return ref_date
    
    # Resolving weekends to the upcoming Saturday
    if text_lower == "this weekend":
        return ref_date + datetime.timedelta(days=_get_weekday_offset(ref_date, 5))
    if text_lower == "next weekend":
        return ref_date + datetime.timedelta(days=_get_weekday_offset(ref_date, 5) + 7)
    
    # Custom foreign language overrides
    if text_lower == "kal" and "hi" in langs:
        return ref_date + datetime.timedelta(days=1)

    # Handle compound relative synonyms (e.g., "Friday next week")
    if "next week" in text_lower:
        part = text_lower.replace("next week", "").strip()
        if part in WEEKDAYS:
            days = _get_weekday_offset(ref_date, WEEKDAYS[part])
            if days == 0:
                days = 7
            return ref_date + datetime.timedelta(days=days + 7)

    # Handle bare weekdays or "this [weekday]" (e.g., "this Monday")
    match_this = re.fullmatch(r'(this\s+)?([a-z]+)', text_lower)
    if match_this and match_this.group(2) in WEEKDAYS:
        target_wd = WEEKDAYS[match_this.group(2)]
        
        # If today is the requested weekday, resolve to today
        if ref_date.weekday() == target_wd:
            return ref_date
        
        days = _get_weekday_offset(ref_date, target_wd)
        if days == 0:
            days = 7
        return ref_date + datetime.timedelta(days=days)

    # Handle "next [weekday]" which skips to the week after
    match_next = re.fullmatch(r'next\s+([a-z]+)', text_lower)
    if match_next and match_next.group(1) in WEEKDAYS:
        target_wd = WEEKDAYS[match_next.group(1)]
        days = _get_weekday_offset(ref_date, target_wd)
        if days == 0:
            days = 7
        return ref_date + datetime.timedelta(days=days + 7)

    # Handle ordinal day references (e.g., "the 15th")
    ordinal_match = re.fullmatch(r'the\s+(\d+)(st|nd|rd|th)', text_lower)
    if ordinal_match:
        day = int(ordinal_match.group(1))
        
        # If the day has already passed in the current month, roll over to the next month
        if day < ref_date.day:
            month = ref_date.month + 1
            year = ref_date.year
            if month > 12:
                month = 1
                year += 1  # Roll over to January of the next year if we hit month 13
            try:
                return datetime.date(year, month, day)
            except ValueError:
                pass
        else:
            try:
                return datetime.date(ref_date.year, ref_date.month, day)
            except ValueError:
                pass

    # Fast-track valid ISO 8601 datetimes to bypass dateparser strictness limitations
    iso_match = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})(?:T.*)?', text, re.IGNORECASE)
    if iso_match:
        try:
            return datetime.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        except ValueError:
            pass

    # Fallback to the third-party dateparser for complex/standard inputs
    try:
        dt = dateparser.parse(text, languages=langs, settings={
            'TIMEZONE': tz,
            'RETURN_AS_TIMEZONE_AWARE': False,
            'PREFER_DATES_FROM': 'future',
            'DATE_ORDER': 'DMY',
            'RELATIVE_BASE': datetime.datetime(ref_date.year, ref_date.month, ref_date.day),
            'STRICT_PARSING': False
        })
        
        if dt:
            return dt.date()
        else:
            logging.warning(f"date_parser rejected input: Unparseable date '{text}'")
            return None
            
    except (ValueError, OverflowError) as e:
        logging.warning(f"date_parser rejected input: Exception '{e}'")
        return None
