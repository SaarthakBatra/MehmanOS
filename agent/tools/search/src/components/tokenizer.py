"""
Tokenizer Component for the Search Module.

Provides functionality for splitting text into words and removing stop words.
"""
import re

STOP_WORDS = {"and", "with", "a", "an", "the", "or", "for", "in", "of"}

def _tokenize(text: str | None) -> list[str]:
    """
    Tokenizes a given string into lowercase words, stripping out common stop words.

    Args:
        text (str | None): The input string to tokenize.

    Returns:
        list[str]: A list of valid lowercase tokens.
    """
    if not text:
        return []
        
    # Extract alphanumeric words and convert to lowercase
    tokens = re.findall(r'\w+', text.lower())
    
    # Exclude predefined stop words to focus on meaningful keywords
    return [t for t in tokens if t not in STOP_WORDS]
