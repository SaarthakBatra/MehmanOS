"""
Orchestrator Router Module.

This module routes calls to the underlying components.
"""

from agent.orchestrator.src.components.client import get_client as _get_client
from agent.orchestrator.src.components.tool_runner import _run_tool as _run_tool_comp, TOOL_SCHEMAS
from agent.orchestrator.src.components.processor import process_turn as _process_turn, TurnResult, OrchestratorConfig

# Export client for test patching

# Exported for test patching
try:
    from agent.recovery.src.recovery import recovery_module
except ImportError:
    recovery_module = None
try:
    import agent.upsell.src.upsell as upselling_module
except ImportError:
    upselling_module = None
from agent.config.src.config import get_settings
client = None


"""
    Retrieves the initialized Gemini API client, instantiating it if necessary.

    Returns:
        google.genai.Client: The active Gemini API client instance.
"""
def get_client():
    return _get_client()

"""
    Executes a booking tool by name, dynamically resolving the implementation.

    Args:
        name (str): The name of the tool to execute.
        kwargs (dict): The arguments to pass to the tool.

    Returns:
        dict: The result of the tool execution.

    Raises:
        ValueError: If the requested tool is not found.
"""
def _run_tool(name: str, kwargs: dict) -> dict:
    return _run_tool_comp(name, kwargs)

"""
    Processes a single conversational turn in the orchestrator, managing state, executing tools, and interacting with the LLM.

    Args:
        session_id (str): The unique identifier for the user's session.
        user_message (str): The input text message from the user.

    Returns:
        TurnResult: An object containing the model's response, the updated state, and any potential upsell suggestions.
"""
def process_turn(session_id: str, user_message: str) -> TurnResult:
    return _process_turn(session_id, user_message)
