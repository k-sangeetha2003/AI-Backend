from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import ModelInfo, LoRAInfo
from app.services.model_manager import ModelManager

router = APIRouter()

model_manager = ModelManager()

@router.get("/models", response_model=List[ModelInfo])
async def get_available_models():
    """
    Get list of available models.
    """
    try:
        models = model_manager.get_available_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/loras", response_model=List[LoRAInfo])
async def get_available_loras():
    """
    Get list of available LoRAs.
    """
    try:
        loras = model_manager.get_available_loras()
        return loras
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}")
async def get_model_info(model_name: str):
    """
    Get detailed information about a specific model.
    """
    try:
        model_info = model_manager.get_model_info(model_name)
        if not model_info:
            raise HTTPException(status_code=404, detail="Model not found")
        return model_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
