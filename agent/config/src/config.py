from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application configuration settings.

    Reads from system environment variables and a local .env file.
    System variables take precedence over the .env file.
    """
    
    # Required field: Gemini API Key
    google_api_key: str = Field(min_length=1)
    
    # Optional fields with predefined default values
    gemini_model: str = "gemini-3.5-flash-lite"
    db_path: Path = Path("data/availability_db/src/availability.db")
    properties_path: Path = Path("data/properties/src/properties.json")
    session_dir: Path = Path("sessions/")
    session_lock_timeout: int = 5
    max_user_input_length: int = 500
    debug: bool = False

    # Configuration for pydantic v2 settings resolution
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # Silently ignores any extra host OS environment variables
        frozen=True      # Enforces strict immutability after instantiation
    )

@lru_cache()
def get_settings() -> Settings:
    """
    Retrieves the application settings singleton.

    Returns:
        Settings: An immutable configuration object containing application settings.
    """
    return Settings()
