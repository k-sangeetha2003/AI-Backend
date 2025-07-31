from pathlib import Path
from typing import List, Dict, Any
import json
import logging

from app.config import settings
from app.models.schemas import ModelInfo, LoRAInfo

logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        self.models_path = Path(settings.models_path)
        self.loras_path = Path(settings.loras_path)
    
    def get_available_models(self) -> List[ModelInfo]:
        """
        List all .safetensors files in the models directory (no subfolders required).
        """
        models = []
        for file in self.models_path.glob("*.safetensors"):
            models.append(ModelInfo(
                name=file.stem,
                type="stable-diffusion",
                description=f"Model file: {file.name}",
                resolution="512x512",
                size=f"{file.stat().st_size // (1024*1024)} MB"
            ))
        return models
    
    def get_available_loras(self) -> List[LoRAInfo]:
        """
        Get list of available LoRAs.
        """
        loras = []
        
        try:
            for lora_file in self.loras_path.glob("*.safetensors"):
                lora_info = LoRAInfo(
                    name=lora_file.stem,
                    description=f"LoRA: {lora_file.stem}",
                    strength=1.0,
                    size=self._format_file_size(lora_file.stat().st_size)
                )
                loras.append(lora_info)
            
            return loras
            
        except Exception as e:
            logger.error(f"Error getting available LoRAs: {e}")
            return []
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        """
        try:
            model_path = self.models_path / model_name
            if not model_path.exists():
                return None
            
            # Get model files
            model_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("*.bin"))
            
            return {
                "name": model_name,
                "path": str(model_path),
                "files": [f.name for f in model_files],
                "size": self._get_directory_size(model_path),
                "type": "stable-diffusion"
            }
            
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None
    
    def _get_directory_size(self, path: Path) -> str:
        """
        Get directory size in human readable format.
        """
        total_size = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return self._format_file_size(total_size)
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human readable format.
        """
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
