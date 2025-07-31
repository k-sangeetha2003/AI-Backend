from typing import List
import re
from pathlib import Path

from app.models.schemas import GenerationRequest
from app.config import settings

def validate_generation_request(request: GenerationRequest) -> bool:
    """
    Validate generation request parameters.
    """
    # Validate prompt
    if not request.prompt or len(request.prompt.strip()) == 0:
        raise ValueError("Prompt cannot be empty")
    
    if len(request.prompt) > 1000:
        raise ValueError("Prompt too long (max 1000 characters)")
    
    # Validate model
    model_path = Path(settings.models_path) / request.model_name
    if not model_path.exists():
        raise ValueError(f"Model '{request.model_name}' not found")
    
    # Validate LoRA if provided
    if request.lora_name:
        lora_path = Path(settings.loras_path) / f"{request.lora_name}.safetensors"
        if not lora_path.exists():
            raise ValueError(f"LoRA '{request.lora_name}' not found")
    
    # Validate resolution
    try:
        width, height = map(int, request.resolution.split('x'))
        if not (64 <= width <= 2048 and 64 <= height <= 2048):
            raise ValueError("Resolution must be between 64x64 and 2048x2048")
        if width % 8 != 0 or height % 8 != 0:
            raise ValueError("Resolution must be multiples of 8")
    except (ValueError, AttributeError):
        raise ValueError("Invalid resolution format")
    
    # Validate inference steps
    if not (1 <= request.num_inference_steps <= 100):
        raise ValueError("num_inference_steps must be between 1 and 100")
    
    # Validate guidance scale
    if not (1.0 <= request.guidance_scale <= 20.0):
        raise ValueError("guidance_scale must be between 1.0 and 20.0")
    
    return True

def validate_prompt_safety(prompt: str) -> bool:
    """
    Basic prompt safety validation.
    """
    # Check for empty or whitespace-only prompts
    if not prompt or len(prompt.strip()) == 0:
        return False
    
    # Check for excessive length
    if len(prompt) > 1000:
        return False
    
    # Check for suspicious patterns
    suspicious_patterns = [
        r'<script>',
        r'javascript:',
        r'data:text/html',
        r'vbscript:',
        r'onload=',
        r'onerror='
    ]
    
    for pattern in suspicious_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            return False
    
    return True
