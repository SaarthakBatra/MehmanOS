"""
Core intent detection logic.
"""
import logging
import re

from .config import _compiled_patterns
from .types import DetectedIntent, IntentLabel

logger = logging.getLogger(__name__)

def detect_intent(user_message: str, max_length: int = 500) -> DetectedIntent:
    """
    Analyzes a user message to classify their primary intent using heuristic regex pattern matching.
    
    Args:
        user_message (str): The raw input message from the user.
        max_length (int, optional): The maximum character threshold before bypassing regex and 
                                    returning INPUT_TOO_LONG (ReDoS protection). Defaults to 500.
                                    
    Returns:
        DetectedIntent: Contains the resolved intent (IntentLabel) and a binary confidence score.
        
    Raises:
        TypeError: If the caller passes a non-string user_message.
    """
    # Enforce strict caller contract to prevent downstream type errors
    if not isinstance(user_message, str):
        raise TypeError("user_message must be a string")
        
    # ReDoS protection: bypass regex evaluation entirely if input exceeds length threshold
    if len(user_message) > max_length:
        logger.warning("intent_detector: ReDoS threshold exceeded. Input rejected.")
        return DetectedIntent(intent="INPUT_TOO_LONG", confidence=1.0)
        
    # Safe fallback for empty or whitespace-only inputs without triggering OUT_OF_SCOPE
    if not user_message or not user_message.strip():
        return DetectedIntent(intent="NONE", confidence=0.0)
        
    # Normalization: Lowercase and strip terminal/surrounding punctuation (!, ?, etc.)
    normalized = user_message.lower()
    normalized = re.sub(r"^[^\w\s]+|[^\w\s]+$", "", normalized)
    
    # Collapse all consecutive whitespace characters (tabs, newlines, multiple spaces) into a single space
    normalized = re.sub(r"\s+", " ", normalized).strip()
    
    # Evaluate strictly in priority order. NONE is omitted as it is handled by the final fallback.
    priority_order: list[IntentLabel] = [
        "INPUT_TOO_LONG",
        "OUT_OF_SCOPE",
        "STATE_UPDATE",
        "GET_POLICY",
        "SEARCH_AND_VALIDATE",
        "CHECK_AVAILABILITY",
        "UPSELL_TRIGGER"
    ]
    
    for intent in priority_order:
        for pattern in _compiled_patterns.get(intent, []):
            if pattern.search(normalized):
                # Return immediately on first match based on the priority hierarchy
                return DetectedIntent(intent=intent, confidence=1.0)
                
    # Fallback to zero-confidence NONE when no heuristic patterns match
    return DetectedIntent(intent="NONE", confidence=0.0)

