from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
from datetime import datetime

from app.models.schemas import GenerationRequest, GenerationResponse
from app.services.image_generator import ImageGenerator
from app.services.guardrails import SafetyService
from app.services.session_manager import SessionManager
from app.utils.validators import validate_generation_request

router = APIRouter()

# Initialize services
image_generator = ImageGenerator()
safety_service = SafetyService()
session_manager = SessionManager()

@router.post("/generate", response_model=GenerationResponse)
async def generate_image(
    request: GenerationRequest,
    session_id: str = None
):
    """
    Generate an image from text prompt.
    
    - **prompt**: Text description of the image
    - **model_name**: Name of the model to use
    - **lora_name**: Optional LoRA to apply
    - **negative_prompt**: Optional negative prompt
    - **resolution**: Image resolution (e.g., "512x512")
    - **seed**: Random seed for reproducible results
    """
    # Safety check before generation
    is_safe, reason = safety_service.is_safe(request.prompt)
    if not is_safe:
        raise HTTPException(status_code=400, detail=reason)
    try:
        # Validate request
        validate_generation_request(request)
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Generate image
        result = await image_generator.generate(
            prompt=request.prompt,
            model_name=request.model_name,
            lora_name=request.lora_name,
            negative_prompt=request.negative_prompt,
            resolution=request.resolution,
            seed=request.seed,
            num_inference_steps=request.num_inference_steps,
            guidance_scale=request.guidance_scale,
            session_id=session_id
        )
        
        # Update session
        session_manager.update_session(session_id, "image_generated")
        
        return GenerationResponse(
            success=True,
            image_path=result["image_path"],
            download_url=f"/outputs/{result['filename']}",
            metadata=result["metadata"],
            message="Image generated successfully",
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-prompt")
async def enhance_prompt(prompt: str):
    """
    Enhance a prompt to make it more detailed and creative.
    """
    try:
        enhanced_prompt = await image_generator.enhance_prompt(prompt)
        return {
            "success": True,
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
