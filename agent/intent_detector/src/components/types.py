"""
Type definitions for the intent detector module.
"""
from dataclasses import dataclass
from typing import Literal

IntentLabel = Literal[
    "OUT_OF_SCOPE",
    "STATE_UPDATE",
    "GET_POLICY",
    "SEARCH_AND_VALIDATE",
    "CHECK_AVAILABILITY",
    "UPSELL_TRIGGER",
    "INPUT_TOO_LONG",
    "NONE"
]

IntentConfig = dict[IntentLabel, list[str]]

@dataclass(frozen=True)
class DetectedIntent:
    """
    Immutable representation of a resolved intent and its confidence score.
    """
    intent: IntentLabel
    confidence: float
