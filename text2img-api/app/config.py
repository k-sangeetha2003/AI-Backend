from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import os

class Settings(BaseModel):
    # Application settings
    app_name: str = "Text-to-Image API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Paths
    models_path: str = "./models"
    loras_path: str = "./loras"
    outputs_path: str = "./outputs"
    data_path: str = "./data"
    
    # Security
    secret_key: str = "your-secret-key-change-this-in-production"
    jwt_secret: str = "your-jwt-secret-change-this-in-production"
    
    # Generation settings
    default_resolution: tuple[int, int] = (512, 512)
    max_resolution: tuple[int, int] = (1024, 1024)
    min_resolution: tuple[int, int] = (256, 256)
    
    # Safety settings
    enable_safety_checks: bool = True
    nsfw_filter_enabled: bool = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.app_name = os.getenv("APP_NAME", self.app_name)
        self.app_version = os.getenv("APP_VERSION", self.app_version)
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.api_host = os.getenv("API_HOST", self.api_host)
        self.api_port = int(os.getenv("API_PORT", self.api_port))
        self.api_workers = int(os.getenv("API_WORKERS", self.api_workers))
        self.models_path = os.getenv("MODELS_PATH", self.models_path)
        self.loras_path = os.getenv("LORAS_PATH", self.loras_path)
        self.outputs_path = os.getenv("OUTPUTS_PATH", self.outputs_path)
        self.data_path = os.getenv("DATA_PATH", self.data_path)
        self.secret_key = os.getenv("SECRET_KEY", self.secret_key)
        self.jwt_secret = os.getenv("JWT_SECRET", self.jwt_secret)

# Create settings instance
settings = Settings()

# Ensure directories exist
for path in [settings.models_path, settings.loras_path, settings.outputs_path, settings.data_path]:
    Path(path).mkdir(parents=True, exist_ok=True)
