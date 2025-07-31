from fastapi import APIRouter, HTTPException
from typing import List
import os
from pathlib import Path

from app.config import settings

router = APIRouter()

@router.get("/images")
async def get_all_images():
    """
    Get list of all generated images.
    """
    try:
        output_path = Path(settings.outputs_path)
        images = []
        
        for file_path in output_path.glob("*.png"):
            images.append({
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "created_at": file_path.stat().st_ctime,
                "url": f"/outputs/{file_path.name}"
            })
        
        return {
            "success": True,
            "images": images,
            "count": len(images)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/images/{filename}")
async def delete_image(filename: str):
    """
    Delete a specific image.
    """
    try:
        file_path = Path(settings.outputs_path) / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Image not found")
        
        file_path.unlink()
        return {
            "success": True,
            "message": f"Image {filename} deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/images")
async def delete_all_images():
    """
    Delete all generated images.
    """
    try:
        output_path = Path(settings.outputs_path)
        deleted_count = 0
        
        for file_path in output_path.glob("*.png"):
            file_path.unlink()
            deleted_count += 1
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} images successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
