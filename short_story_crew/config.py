import os
from typing import Any, Dict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # API Keys - Support both OpenAI and OpenRouter
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    # Project Settings
    MAX_STORY_DURATION = int(os.getenv("MAX_STORY_DURATION", "15"))
    PROJECT_NAME = os.getenv("PROJECT_NAME", "short_story_crew")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # LLM Provider Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # "openai" or "openrouter"
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    # Model assignments for different crew members
    CREW_MODELS = {
        "director": os.getenv("DIRECTOR_MODEL", "gpt-4o"),
        "story_writer": os.getenv("STORY_WRITER_MODEL", "gpt-4"),
        "proofreader": os.getenv("PROOFREADER_MODEL", "gpt-4o-mini"),
        "art_designer": os.getenv("ART_DESIGNER_MODEL", "claude-3.5-sonnet"),
        "script_coordinator": os.getenv("SCRIPT_COORDINATOR_MODEL", "gpt-4"),
    }

    # OpenRouter model mappings
    OPENROUTER_MODELS = {
        "gpt-4o": "openai/gpt-4o",
        "gpt-4": "openai/gpt-4-turbo",
        "gpt-4o-mini": "openai/gpt-4o-mini",
        "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
        "claude-3-opus": "anthropic/claude-3-opus",
        "gemini-pro": "google/gemini-pro",
    }

    # Temperature settings for different roles
    CREW_TEMPERATURES = {
        "director": 0.8,  # More creative for vision setting
        "story_writer": 0.9,  # High creativity for story creation
        "proofreader": 0.3,  # Lower for precision editing
        "art_designer": 0.8,  # Creative for visual descriptions
        "script_coordinator": 0.5,  # Balanced for organization
    }

    # Supported story genres
    SUPPORTED_GENRES = [
        "drama",
        "comedy",
        "romance",
        "thriller",
        "horror",
        "sci-fi",
        "fantasy",
        "action",
        "adventure",
        "mystery",
        "family",
        "kids",
        "anime",
        "manga",
        "motivational",
        "inspirational",
        "educational",
        "documentary",
        "experimental",
        "noir",
        "western",
        "musical",
        "biographical",
        "historical",
    ]

    @classmethod
    def get_api_key(cls) -> str:
        """Get the appropriate API key based on LLM provider."""
        if cls.LLM_PROVIDER.lower() == "openrouter":
            return cls.OPENROUTER_API_KEY
        else:
            return cls.OPENAI_API_KEY

    @classmethod
    def get_model_for_crew(cls, crew_member: str) -> str:
        """Get the model name for a specific crew member."""
        model = cls.CREW_MODELS.get(crew_member, "gpt-4")

        # Convert to OpenRouter format if using OpenRouter
        if cls.LLM_PROVIDER.lower() == "openrouter":
            return cls.OPENROUTER_MODELS.get(model, f"openai/{model}")

        return model

    @classmethod
    def get_temperature_for_crew(cls, crew_member: str) -> float:
        """Get the temperature setting for a specific crew member."""
        return cls.CREW_TEMPERATURES.get(crew_member, 0.7)

    @classmethod
    def get_llm_config(cls, crew_member: str) -> Dict[str, Any]:
        """Get complete LLM configuration for a crew member."""
        config = {
            "model": cls.get_model_for_crew(crew_member),
            "temperature": cls.get_temperature_for_crew(crew_member),
            "api_key": cls.get_api_key(),
        }

        # Add base URL for OpenRouter
        if cls.LLM_PROVIDER.lower() == "openrouter":
            config["base_url"] = cls.OPENROUTER_BASE_URL

        return config

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        api_key = cls.get_api_key()
        if not api_key:
            provider = cls.LLM_PROVIDER.upper()
            key_name = f"{provider}_API_KEY"
            raise ValueError(
                f"{key_name} environment variable is required for {provider} provider"
            )

        # Validate genre support
        if not cls.SUPPORTED_GENRES:
            raise ValueError("No supported genres configured")

        return True
