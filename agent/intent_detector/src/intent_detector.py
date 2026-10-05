"""
Router for intent detection module. Exposes the core components.
"""
from .components.types import IntentLabel, IntentConfig, DetectedIntent
from .components import config
from .components import detector

if 'INTENT_CONFIG' not in globals():
    INTENT_CONFIG = config.INTENT_CONFIG

"""
Compiles regex patterns from a configuration dictionary and stores them in a private module cache.

Args:
    config_dict (dict): A dictionary mapping IntentLabel to lists of string regex patterns.
    
Raises:
    ValueError: If a pattern is not a string, or if regex compilation fails (Fail-Fast).
"""
def _initialize_intent_config(config_dict: dict) -> None:
    return config._initialize_intent_config(config_dict)

# Initialize on module load with whatever INTENT_CONFIG is currently set to in globals
_initialize_intent_config(INTENT_CONFIG)


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
def detect_intent(user_message: str, max_length: int = 500) -> DetectedIntent:
    return detector.detect_intent(user_message, max_length)
