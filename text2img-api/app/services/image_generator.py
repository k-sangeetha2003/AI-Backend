import os
from pathlib import Path
import uuid
from datetime import datetime
import logging
from PIL import Image, ImageDraw, ImageFont
import random
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline
import torch
from typing import Optional
from pydantic import Field

from app.config import settings

logger = logging.getLogger(__name__)

def get_pipeline(model_path):
    # Use SDXL pipeline for SDXL models, otherwise use SD pipeline
    if "xl" in str(model_path).lower():
        return StableDiffusionXLPipeline
    else:
        return StableDiffusionPipeline

class ImageGenerator:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipelines = {}
        
    async def generate(
        self,
        prompt: str,
        model_name: str,
        lora_name: str = None,
        negative_prompt: str = "",
        resolution: str = "1024x1024",
        seed: int = None,
        num_inference_steps: int = 40,
        guidance_scale: float = 9.0,
        session_id: str = None
    ):
        """
        Generate a placeholder image (for testing purposes).
        In production, this would use actual Stable Diffusion.
        """
        try:
            # Parse resolution
            width, height = map(int, resolution.split('x'))
            
            # Set seed for reproducibility
            if seed is not None:
                torch.manual_seed(seed)
            
            # Load model
            model_path = Path(settings.models_path) / model_name
            logger.info(f"Looking for model at: {model_path}")
            if not model_path.exists():
                raise ValueError(f"Model {model_name} not found")
            # Load pipeline if not already loaded
            if model_name not in self.pipelines:
                pipeline_cls = get_pipeline(model_path)
                pipe = pipeline_cls.from_single_file(
                    str(model_path),
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                pipe = pipe.to(self.device)
                self.pipelines[model_name] = pipe
            pipe = self.pipelines[model_name]
            
            # Load and apply LoRA if lora_name is provided
            if lora_name and lora_name.lower() not in ["null", "none", "string", ""]:
                # Load and apply LoRA
                ...
            # Otherwise, skip LoRA
            
            # Generate image
            image = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
            ).images[0]
            
            # Save image
            filename = f"{uuid.uuid4()}.png"
            output_path = Path(settings.outputs_path) / filename
            image.save(output_path)
            
            # Prepare metadata
            metadata = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model_name,
                "lora": lora_name,
                "resolution": resolution,
                "seed": seed,
                "num_inference_steps": num_inference_steps,
                "guidance_scale": guidance_scale,
                "session_id": session_id,
                "generated_at": datetime.utcnow().isoformat(),
                "note": "This is a placeholder image for testing"
            }
            
            return {
                "image_path": str(output_path),
                "filename": filename,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    def _create_placeholder_image(self, prompt: str, width: int, height: int) -> Image.Image:
        """
        Create a placeholder image with the prompt text.
        """
        # Create a new image with a gradient background
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Create a simple gradient background
        for y in range(height):
            r = int(255 * (1 - y / height))
            g = int(200 * (y / height))
            b = int(255 * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        # Add text
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add prompt text
        text = f"Generated: {prompt[:50]}..."
        if len(prompt) > 50:
            text += "..."
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw text with outline
        draw.text((x+2, y+2), text, fill='black', font=font)
        draw.text((x, y), text, fill='white', font=font)
        
        return image
    
    async def enhance_prompt(self, prompt: str) -> str:
        """
        Enhance a prompt to make it more detailed and creative.
        """
        # Simple prompt enhancement logic
        enhancements = [
            "high quality, detailed, professional",
            "beautiful lighting, cinematic",
            "masterpiece, best quality",
            "sharp focus, high resolution"
        ]
        
        enhanced_prompt = f"{prompt}, {', '.join(enhancements)}"
        return enhanced_prompt
