from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class ResolutionEnum(str, Enum):
    """Predefined resolution options."""
    SMALL = "256x256"
    MEDIUM = "512x512"
    LARGE = "768x768"
    XLARGE = "1024x1024"

class GenerationRequest(BaseModel):
    """Request model for image generation."""
    prompt: str
    model_name: str
    negative_prompt: Optional[str] = ""
    lora_name: Optional[str] = Field(default=None, description="Optional LoRA to apply. Leave blank if not using a LoRA.")
    resolution: str = "1024x1024"
    num_inference_steps: int = 40
    guidance_scale: float = 9.0
    seed: Optional[int] = None
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Validate resolution format."""
        try:
            width, height = map(int, v.split('x'))
            if not (64 <= width <= 2048 and 64 <= height <= 2048):
                raise ValueError('Resolution must be between 64x64 and 2048x2048')
            if width % 8 != 0 or height % 8 != 0:
                raise ValueError('Resolution must be multiples of 8')
            return v
        except (ValueError, AttributeError):
            raise ValueError('Resolution must be in format "WIDTHxHEIGHT"')

    model_config = {
        "protected_namespaces": ()
    }

class GenerationResponse(BaseModel):
    """Response model for image generation."""
    success: bool
    image_path: Optional[str] = None
    download_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    message: str = ""
    timestamp: str = ""

class ModelInfo(BaseModel):
    """Model information."""
    name: str
    type: str
    description: str
    resolution: str
    size: str

class LoRAInfo(BaseModel):
    """LoRA information."""
    name: str
    description: str
    strength: float
    size: str

class SessionInfo(BaseModel):
    """Session information."""
    session_id: str
    created_at: datetime
    images_generated: int
    last_activity: datetime

class SafetyResult(BaseModel):
    """Safety check result."""
    is_safe: bool
    reason: str = ""
    category: str = ""
    confidence: float = 0.0
