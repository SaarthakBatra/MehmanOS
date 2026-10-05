"""
Configuration and initialization logic for intent patterns.
"""
import re

from .types import IntentConfig, IntentLabel

INTENT_CONFIG: IntentConfig = {
    "OUT_OF_SCOPE": [r"ignore previous instructions", r"system prompt", r"airbnb", r"oyo"],
    "STATE_UPDATE": [r"actually", r"change that to", r"make it", r"instead"],
    "GET_POLICY": [r"cancel", r"pet", r"pets", r"refund", r"check-in time"],
    "SEARCH_AND_VALIDATE": [r"search", r"find", r"looking for", r"options"],
    "CHECK_AVAILABILITY": [r"book", r"reserve", r"available", r"availability"],
    "UPSELL_TRIGGER": [r"add-ons", r"extras", r"anything else", r"airport pickup"],
    "INPUT_TOO_LONG": [],
    "NONE": []
}

_compiled_patterns: dict[IntentLabel, list[re.Pattern]] = {}

def _initialize_intent_config(config_dict: dict) -> None:
    """
    Compiles regex patterns from a configuration dictionary and stores them in a private module cache.
    
    Args:
        config_dict (dict): A dictionary mapping IntentLabel to lists of string regex patterns.
        
    Raises:
        ValueError: If a pattern is not a string, or if regex compilation fails (Fail-Fast).
    """
    global _compiled_patterns
    _compiled_patterns.clear()  # Reset cache for clean re-initialization
    
    # Priority defines the evaluation order for intent classification
    priority_order: list[IntentLabel] = [
        "INPUT_TOO_LONG",
        "OUT_OF_SCOPE",
        "STATE_UPDATE",
        "GET_POLICY",
        "SEARCH_AND_VALIDATE",
        "CHECK_AVAILABILITY",
        "UPSELL_TRIGGER",
        "NONE"
    ]
    
    for intent in priority_order:
        patterns = config_dict.get(intent, [])
        compiled_list = []
        for p in patterns:
            # Enforce strict type safety on configuration strings
            if not isinstance(p, str):
                raise ValueError(f"Pattern {p} must be a string")
            
            try:
                # Wrap patterns with \b for strict word boundaries to prevent substring false positives
                compiled = re.compile(rf"\b{p}\b")
                compiled_list.append(compiled)
            except re.error as e:
                # Fail-fast on invalid regex to prevent silently broken routers
                raise ValueError(f"Invalid regex pattern: {p}") from e
                
        # Cache the compiled pattern list for efficient sequential matching
        _compiled_patterns[intent] = compiled_list
