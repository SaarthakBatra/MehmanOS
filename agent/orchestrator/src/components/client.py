"""
Provides the Gemini API client initialization and management.
"""
import logging
import google.genai
from agent.config.src.config import get_settings


logger = logging.getLogger(__name__)


class DummyModels:
    """Mock models interface for offline development."""
    
    def generate_content(self, *args, **kwargs):
        return None


class DummyClient:
    """Mock Gemini client structure."""
    
    def __init__(self):
        self.models = DummyModels()


client = DummyClient()


def get_client() -> google.genai.Client:
    """
    Retrieve or initialize the global Gemini client.
    Supports dynamic patching in test environments.
    """
    # Allow tests to patch 'client' in the main orchestrator router
    try:
        import agent.orchestrator.src.orchestrator as orch
        if hasattr(orch, 'client') and orch.client is not None and not isinstance(orch.client, DummyClient):
            return orch.client
    except ImportError:
        pass
        
    global client
    
    # Initialize the real client if we are using the dummy placeholder
    if client is None or isinstance(client, DummyClient):
        settings = get_settings()
        client = google.genai.Client(api_key=settings.google_api_key)
        
    return client
