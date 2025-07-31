# main.py - FastAPI backend for offline Image-to-Image generation with multilingual, face-preserving, prompt-based support

import os
import io
import uuid
import json
import torch
import logging
import base64
import hashlib
import numpy as np
from enum import Enum
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionXLImg2ImgPipeline
import cv2
import sys
from typing import Optional

# Set up logging BEFORE using logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add this at the top of your file after imports but before other setup
def create_fallback_pipeline():
    """Create a simple fallback pipeline for testing"""
    try:
        # Temporarily go online
        os.environ["HF_HUB_OFFLINE"] = "0"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        
        from diffusers import DiffusionPipeline
        
        # Download a small model that works reliably
        pipe = DiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5", 
            torch_dtype=torch.float32,
            variant="fp16",
            safety_checker=None,
        )
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()
        
        # Save it locally
        pipe.save_pretrained("./base_models/fallback_pipeline")
        
        # Restore offline mode
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        return pipe
    except Exception as e:
        logger.error(f"Failed to create fallback pipeline: {e}")
        return None

# Create a small generic fallback model
try:
    fallback_pipe = create_fallback_pipeline()
    if fallback_pipe:
        logger.info("Successfully created fallback pipeline")
    else:
        logger.warning("Failed to create fallback pipeline")
except Exception as e:
    logger.warning(f"Error creating fallback pipeline: {e}")

# Set offline and performance-related environment variables
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Add this function to help with offline loading
def setup_offline_dependencies():
    """Download required files for offline usage"""
    try:
        # Temporarily switch to online mode
        original_hf_offline = os.environ.get("HF_HUB_OFFLINE")
        original_transformers_offline = os.environ.get("TRANSFORMERS_OFFLINE")
        
        os.environ["HF_HUB_OFFLINE"] = "0"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        
        logger.info("Downloading required components for offline use...")
        from transformers import CLIPTextModel, CLIPTokenizer
        
        # Download tokenizer and text encoder
        CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
        CLIPTextModel.from_pretrained("openai/clip-vit-large-patch14")
        
        logger.info("Components downloaded successfully")
        
        # Restore offline settings
        if original_hf_offline:
            os.environ["HF_HUB_OFFLINE"] = original_hf_offline
        if original_transformers_offline:
            os.environ["TRANSFORMERS_OFFLINE"] = original_transformers_offline
            
    except Exception as e:
        logger.warning(f"Could not download components: {e}")

# Add this function and call it before loading any models
def extract_model_components():
    base_dir = Path("base_models")
    base_dir.mkdir(exist_ok=True)
    
    # Create SD 1.5 structure
    sd15_dir = base_dir / "stable-diffusion-v1-5"
    sd15_dir.mkdir(exist_ok=True)
    
    # If you have standalone text_encoder/tokenizer files, copy them here
    return

# Call the function (will run once on startup)
setup_offline_dependencies()

# Directories
# Use D: drive exclusively - outputs will be visible in VS Code
project_dir = Path("D:/sangeetha/mirage-ai-project-clean/mirage-ai-project1")
if not project_dir.exists():
    logger.error(f"Project directory {project_dir} not found!")
    # Fall back to current directory as last resort
    project_dir = Path.cwd()

UPLOAD_DIR = project_dir / "uploads"
OUTPUT_DIR = project_dir / "outputs"
MODEL_DIR = project_dir / "models"
LORA_DIR = project_dir / "loras"

for path in [UPLOAD_DIR, OUTPUT_DIR, MODEL_DIR, LORA_DIR]:
    path.mkdir(exist_ok=True)

logger.info(f"Using project directory for all files: {project_dir}")
logger.info(f"Outputs will be saved to: {OUTPUT_DIR}")

def check_disk_space(directory_path, required_mb=100):
    """Check if there's enough disk space available"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(directory_path)
        free_mb = free / (1024 * 1024)  # Convert to MB
        
        if free_mb < required_mb:
            logger.warning(f"Low disk space warning: Only {free_mb:.2f}MB available on {directory_path}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking disk space: {e}")
        return False

def cleanup_old_files(directory, keep_days=2, min_required_mb=200):
    """Delete old files to free up disk space"""
    try:
        import shutil
        import time
        
        # Check current free space
        total, used, free = shutil.disk_usage(directory)
        free_mb = free / (1024 * 1024)  # Convert to MB
        
        # If we already have enough space, no need to clean up
        if free_mb >= min_required_mb:
            return True
            
        now = time.time()
        deleted_count = 0
        deleted_bytes = 0
        
        # Sort files by modification time (oldest first)
        files = sorted(Path(directory).glob("*.*"), key=lambda x: x.stat().st_mtime)
        
        for file_path in files:
            # Skip if file is less than keep_days old
            if (now - file_path.stat().st_mtime) < keep_days * 86400:
                continue
                
            # Delete the file
            file_size = file_path.stat().st_size
            file_path.unlink()
            deleted_count += 1
            deleted_bytes += file_size
            
            # Check if we've freed enough space
            if (free_mb + (deleted_bytes / (1024 * 1024))) >= min_required_mb:
                break
                
        logger.info(f"Cleaned up {deleted_count} files ({deleted_bytes/(1024*1024):.2f}MB) from {directory}")
        return True
    except Exception as e:
        logger.error(f"Error cleaning up files: {e}")
        return False

def cleanup_project_files(days_to_keep=1):
    """Clean up older files but keep very recent ones"""
    import time
    
    now = time.time()
    cutoff_time = now - (days_to_keep * 86400)  # Convert days to seconds
    deleted_count = 0
    deleted_bytes = 0
    
    # Clean only outputs and uploads, not model files
    for directory in [OUTPUT_DIR, UPLOAD_DIR]:
        for file_path in directory.glob("*.*"):
            try:
                # Skip very recent files
                if file_path.stat().st_mtime > cutoff_time:
                    continue
                    
                file_size = file_path.stat().st_size
                file_path.unlink()
                deleted_count += 1
                deleted_bytes += file_size
            except:
                pass
    
    logger.info(f"Cleaned up {deleted_count} files ({deleted_bytes/(1024*1024):.2f}MB)")
    return deleted_bytes

def emergency_cleanup():
    """Aggressive cleanup for critical disk space situations"""
    try:
        # Delete ALL files in outputs and uploads
        for file in OUTPUT_DIR.glob("*"):
            try:
                file.unlink()
            except:
                pass
        
        for file in UPLOAD_DIR.glob("*"):
            try:
                file.unlink()
            except:
                pass
                
        # Attempt to clear torch cache
        if hasattr(torch, 'cuda') and torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        logger.info("Performed emergency cleanup of all outputs and uploads")
        return True
    except Exception as e:
        logger.error(f"Emergency cleanup failed: {e}")
        return False

# FastAPI app init
app = FastAPI(title="Image-to-Image API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Enum for languages
class Language(str, Enum):
    EN = "en"
    ES = "es"
    FR = "fr"
    DE = "de"
    JA = "ja"
    ZH = "zh"

# Prompt translations
TRANSLATIONS = {
    "en": "photo quality",
    "es": "calidad fotográfica",
    "fr": "qualité photo",
    "de": "Fotoqualität",
    "ja": "写真質のクオリティ",
    "zh": "照片质量"
}

def translate_prompt(prompt: str, lang: Language) -> str:
    quality_tag = TRANSLATIONS.get(lang, "photo quality")
    extras = "ultra realistic, photorealistic, high resolution, 8k, sharp focus, cinematic lighting"
    return f"{prompt}, {quality_tag}, {extras}"


# Pydantic model for generation request
class GenerationRequest(BaseModel):
    prompt: str
    model_id: str
    strength: float = 0.65
    guidance_scale: float = 7.5
    steps: int = 30
    language: Language = Language.EN

# Face detection util
class FacePreserver:
    def __init__(self):
        self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def detect_faces(self, image: Image.Image):
        img = np.array(image.convert("RGB"))[:, :, ::-1]  # PIL to BGR
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return self.detector.detectMultiScale(gray, 1.1, 4)

face_preserver = FacePreserver()

def create_face_mask(image, faces, padding=30):
    """Create a mask that preserves faces more strictly"""
    mask = Image.new('L', image.size, 0)  # Black mask = areas that can change
    draw = ImageDraw.Draw(mask)
    
    for (x, y, w, h) in faces:
        # Draw white rectangle (protected area) around each face with padding
        draw.rectangle([
            max(0, x - padding), 
            max(0, y - padding),
            min(image.width, x + w + padding), 
            min(image.height, y + h + padding)
        ], fill=255)
    
    # Apply feathering to the mask edges for smoother blending
    mask = mask.filter(ImageFilter.GaussianBlur(radius=15))
    return mask

def create_enhanced_face_mask(image, faces, padding=80, feather=30):
    """Create an enhanced mask with better face preservation"""
    mask = Image.new('L', image.size, 0)  # Black mask (areas that can change)
    draw = ImageDraw.Draw(mask)
    
    for (x, y, w, h) in faces:
        # Calculate face center for padding based on face dimensions
        face_center_x = x + w/2
        face_center_y = y + h/2
        
        # Calculate expanded area with more padding for forehead and chin
        padding_top = padding * 1.5  # More padding for hair
        padding_bottom = padding * 1.2  # More padding for chin/neck
        padding_sides = padding * 1.0  # Standard padding for sides
        
        # Draw white rectangle (protected area) with variable padding
        draw.rectangle([
            max(0, x - padding_sides),
            max(0, y - padding_top),
            min(image.width, x + w + padding_sides),
            min(image.height, y + h + padding_bottom)
        ], fill=255)
    
    # Apply gaussian blur for smooth transitions
    mask = mask.filter(ImageFilter.GaussianBlur(radius=feather))
    
    return mask

def post_process_for_face_similarity(original, generated, faces, face_fidelity=0.9):
    """Post-process the generated image to improve face similarity"""
    # If no faces or face_fidelity is low, just return the generated image
    if len(faces) == 0 or face_fidelity < 0.5:
        return generated
    
    result = generated.copy()
    
    for (x, y, w, h) in faces:
        # Extract face regions
        face_original = original.crop((x, y, x+w, y+h))
        face_generated = generated.crop((x, y, x+w, y+h))
        
        # Create a blend mask for smooth transition
        blend_mask = Image.new('L', (w, h), 0)
        blend_draw = ImageDraw.Draw(blend_mask)
        
        # Draw gradient oval mask
        blend_draw.ellipse([w*0.1, h*0.1, w*0.9, h*0.9], fill=255)
        blend_mask = blend_mask.filter(ImageFilter.GaussianBlur(radius=w//10))
        
        # Blend based on face_fidelity parameter (higher = more original face)
        blend = Image.composite(
            Image.blend(face_generated, face_original, face_fidelity),
            face_generated,
            blend_mask
        )
        
        # Paste the blended face back
        result.paste(blend, (x, y))
    
    return result

def get_error_message(exception):
    """Extract a meaningful error message from an exception"""
    try:
        message = str(exception)
        if not message:
            message = repr(exception)
        if not message:
            message = exception.__class__.__name__
        return message
    except:
        return "Unknown error (unable to get exception details)"

# Model loader
PIPELINE_CACHE = {}

def validate_model_file(model_path: Path):
    """Check if the file is likely a valid SD model"""
    if model_path.suffix == '.safetensors':
        # Check file size - SD models are typically 1.5GB+ for SD1.5, 5GB+ for SDXL
        size_gb = model_path.stat().st_size / (1024**3)
        if size_gb < 1.0:
            logger.warning(f"Model file {model_path.name} is only {size_gb:.1f}GB - might not be a full SD model")
            return False
    return True

def load_pipeline(model_path: Path):
    if model_path not in PIPELINE_CACHE:
        device = "cpu"  # Since you're on CPU
        
        try:
            # Detect if model is SDXL based on file size
            is_xl = model_path.stat().st_size > 5 * (1024**3)  # Over 5GB is likely SDXL
            logger.info(f"Detected model type: {'SDXL' if is_xl else 'SD1.5'}")
            
            if is_xl:
                # Use SDXL pipeline for larger models
                pipe = StableDiffusionXLImg2ImgPipeline.from_single_file(
                    pretrained_model_link_or_path=str(model_path),
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    local_files_only=True
                ).to(device)
            else:
                # Use standard pipeline for smaller models
                pipe = StableDiffusionImg2ImgPipeline.from_single_file(
                    pretrained_model_link_or_path=str(model_path),
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    local_files_only=True
                ).to(device)
            
            # Memory optimization
            pipe.enable_attention_slicing(slice_size=1)
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
            
        PIPELINE_CACHE[model_path] = pipe
        return pipe
    return PIPELINE_CACHE[model_path]

def apply_lora(pipe, lora_id, scale=0.8):
    """Apply a LoRA to the pipeline with improved application"""
    if not lora_id:
        return pipe
        
    lora_path = LORA_DIR / f"{lora_id}.safetensors"
    
    if not lora_path.exists():
        logger.warning(f"LoRA file not found: {lora_path}")
        return pipe
    
    try:
        # Import required modules
        from diffusers.utils import load_torch_file
        import torch
        
        # Load the LoRA weights
        logger.info(f"Loading LoRA weights from {lora_path}")
        state_dict = load_torch_file(lora_path)
        
        # Better LoRA application
        pipe.load_lora_weights(state_dict, adapter_name=lora_id)
        pipe.set_adapters([lora_id], adapter_weights=[scale])
        
        # Enable LoRA for text encoder too (important for high quality results)
        if hasattr(pipe, 'text_encoder_lora_scale'):
            pipe.text_encoder_lora_scale = scale
            
        logger.info(f"LoRA {lora_id} applied successfully with scale {scale}")
        return pipe
    except Exception as e:
        logger.error(f"LoRA application failed: {e}")
        return pipe

def generate_simple_image(prompt, base_image=None):
    """Super simple image generation that should always work"""
    try:
        from diffusers import StableDiffusionPipeline
        
        # Go online briefly
        os.environ["HF_HUB_OFFLINE"] = "0"
        os.environ["TRANSFORMERS_OFFLINE"] = "0"
        
        # Get a very small model
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5", 
            torch_dtype=torch.float32,
            revision="fp16",
            variant="fp16"
        )
        pipe = pipe.to("cpu")
        pipe.enable_attention_slicing()
        
        # Generate a simple image
        if base_image is None:
            result = pipe(prompt, height=256, width=256, num_inference_steps=15).images[0]
        else:
            img2img_pipe = StableDiffusionImg2ImgPipeline(**pipe.components)
            result = img2img_pipe(
                prompt=prompt,
                image=base_image.resize((256, 256)),
                strength=0.3,
                num_inference_steps=10
            ).images[0]
            
        # Reset to offline
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
            
        return result
    except Exception as e:
        logger.error(f"Emergency fallback generation failed: {e}")
        # Create a simple gradient image as ultimate fallback
        img = Image.new('RGB', (512, 512))
        for y in range(512):
            for x in range(512):
                r = int(x/2)
                g = int(y/2) 
                b = 100
                img.putpixel((x, y), (r, g, b))
        return img

def enhance_image_quality(image):
    """Enhance the quality of generated image"""
    # Sharpen the image
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.4)
    
    # Enhance contrast slightly
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.1)
    
    # Boost color slightly
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.1)
    
    return image

@app.post("/generate")
async def generate_image(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    model_id: str = Form(...),
    strength: float = Form(0.45),
    guidance_scale: float = Form(7.5),
    steps: int = Form(40),
    language: Language = Form(Language.EN),
    lora_id: Optional[str] = Form(None),
    lora_scale: float = Form(0.7)
):
    try:
        # Log start of process
        logger.info(f"Starting image generation with model: {model_id}")
        
        # Save input image
        content = await image.read()
        logger.info("Image read successfully")
        
        input_image = Image.open(io.BytesIO(content)).convert("RGB")
        image_id = uuid.uuid4().hex 
        input_path = UPLOAD_DIR / f"{image_id}_input.png"
        input_image.save(input_path)
        logger.info(f"Input image saved to {input_path}")
        
        # Log image dimensions
        width, height = input_image.size
        logger.info(f"Input image dimensions: {width}x{height}")

        # Translate prompt
        final_prompt = translate_prompt(prompt, language)
        logger.info(f"Translated prompt: {final_prompt}")   
        logger.info(f"Final prompt: {final_prompt}")

        # Fix: Always define negative_prompt before using it
        negative_prompt = None

        if not negative_prompt:
            negative_prompt = "blurry, low quality, deformed, distorted face, extra limbs, bad anatomy"


        # Load model - THIS IS LIKELY WHERE IT'S FAILING
        model_path = MODEL_DIR / f"{model_id}.safetensors"
        logger.info(f"Looking for model at: {model_path} (exists: {model_path.exists()})")
        
        if not model_path.exists():
            available_models = [f.stem for f in MODEL_DIR.glob("*.safetensors")]
            logger.error(f"Model not found. Available models: {available_models}")
            raise HTTPException(
                status_code=404, 
                detail=f"Model '{model_id}' not found. Available models: {available_models}"
            )

        # Validate model file
        if not validate_model_file(model_path):
            logger.error(f"Model file validation failed for {model_path.name}")
            raise HTTPException(
                status_code=400,
                detail=f"Model file '{model_path.name}' is invalid or incomplete."
            )

        # Log before pipeline loading
        logger.info(f"Loading pipeline for model: {model_id}")
        try:
            pipe = load_pipeline(model_path)
            # After loading the model
            pipe = load_pipeline(model_path)

            # Validate the pipeline
            if pipe is None:
                raise ValueError("Failed to load model pipeline")

            logger.info(f"Pipeline type: {type(pipe).__name__}")

            # Apply LoRA if specified
            if lora_id:
                logger.info(f"Applying LoRA {lora_id} with scale {lora_scale}")
                pipe = apply_lora(pipe, lora_id, lora_scale)
                if pipe is None:
                    raise ValueError("Failed to apply LoRA")
            logger.info("Pipeline loaded successfully")
        except Exception as pipe_error:
            logger.error(f"Pipeline loading failed: {str(pipe_error)}")
            raise Exception(f"Failed to load model pipeline: {str(pipe_error)}")

        # Apply LoRA if provided
        if lora_id:
            pipe = apply_lora(pipe, lora_id, lora_scale)

        # Face-preserving config
        try:
            faces = face_preserver.detect_faces(input_image)
        except Exception as e:
            logger.warning(f"Face detection failed: {e}, continuing without face detection")
            faces = []

        # Better face preservation
        if len(faces) > 0:
            # Add more specific face-preserving terms
            face_terms = ", perfect face, detailed facial features, photorealistic face, preserve identity"
            if "face" not in final_prompt.lower() and "portrait" not in final_prompt.lower():
                final_prompt += face_terms
            
            # Lower strength even more for face preservation 
            strength = min(strength, 0.4)
            # Increase steps for better detail
            steps = max(steps, 50)
            # Increase CFG for more prompt adherence
            guidance_scale = max(guidance_scale, 8.0)
            
            logger.info(f"Faces detected: {len(faces)}. Adjusted settings for face preservation.")
            
            # Create face mask
            face_mask = create_face_mask(input_image, faces, padding=40)
            
            # Check if we're using SDXL pipeline (which doesn't support mask_image)
            is_xl_pipeline = isinstance(pipe, StableDiffusionXLImg2ImgPipeline)
            
            if is_xl_pipeline:
                # For SDXL, use lower strength without mask
                logger.info("Using SDXL pipeline - cannot use mask_image, using lower strength instead")
                result = pipe(
                    prompt=final_prompt,
                    image=input_image,
                    strength=0.3,  # Very low strength to preserve faces
                    guidance_scale=guidance_scale,
                    num_inference_steps=steps,
                    output_type="pil"
                ).images[0]
            else:
                # For regular SD pipelines, we can use the mask
                logger.info("Using regular SD pipeline with face mask")
                # We need an inpainting pipeline for mask_image
                from diffusers import StableDiffusionInpaintPipeline
                
                try:
                    # Try to convert to inpainting pipeline
                    components = pipe.components
                    inpaint_pipe = StableDiffusionInpaintPipeline(**components)
                    inpaint_pipe.to("cpu")
                    
                    # Use inpainting pipeline with mask
                    result = inpaint_pipe(
                        prompt=final_prompt,
                        image=input_image,
                        mask_image=face_mask,
                        strength=0.35,
                        guidance_scale=guidance_scale,
                        num_inference_steps=steps
                    ).images[0]
                except Exception as e:
                    logger.warning(f"Failed to use inpainting for face preservation: {e}")
                    # Fall back to regular img2img with lower strength
                    result = pipe(
                        prompt=final_prompt,
                        image=input_image,
                        strength=0.3,  # Lower strength to preserve faces
                        guidance_scale=guidance_scale,
                        num_inference_steps=steps,
                        output_type="pil"
                    ).images[0]
        else:
            # Resize input image to higher resolution
            max_size = 768  # Increased from 512
            if input_image.width > max_size or input_image.height > max_size:
                ratio = max_size / max(input_image.width, input_image.height)
                new_width = int(input_image.width * ratio)
                new_height = int(input_image.height * ratio)
                new_width = (new_width // 8) * 8  # Make divisible by 8
                new_height = (new_height // 8) * 8
                input_image = input_image.resize((new_width, new_height), Image.LANCZOS)
                logger.info(f"Resized image to {new_width}x{new_height}")

            # Use simpler generation parameters for reliability
            try:
                logger.info(f"Starting generation with simplified parameters")
                # Better generation parameters
                result = pipe(
                    prompt=f"{final_prompt}, best quality, detailed, high resolution",
                    negative_prompt="blurry, low quality, pixelated, deformed, distorted",
                    image=input_image,
                    strength=strength,
                    guidance_scale=guidance_scale,
                    num_inference_steps=steps,
                    output_type="pil"
                ).images[0]
                logger.info("Generation completed successfully")
                
                # Enhance image quality
                result = enhance_image_quality(result)
            except Exception as gen_error:
                logger.error(f"Generation process failed: {str(gen_error)}")
                
                # Try an even simpler approach with lower resolution
                try:
                    logger.info("Last resort: Creating placeholder image with error message")
                    # Create a simple image with text explaining the error
                    result = Image.new('RGB', (512, 512), color=(240, 240, 240))
                    draw = ImageDraw.Draw(result)
                    
                    # Add error message text to the image
                    error_msg = str(gen_error) if len(str(gen_error)) > 0 else "Unknown error occurred"
                    lines = []
                    curr_line = ""
                    for word in error_msg.split():
                        if len(curr_line + " " + word) < 60:
                            curr_line += " " + word if curr_line else word
                        else:
                            lines.append(curr_line)
                            curr_line = word
                    if curr_line:
                        lines.append(curr_line)
                    
                    # Write each line of the error
                    for i, line in enumerate(lines):
                        draw.text((10, 10 + i*20), line, fill=(0, 0, 0))
                    
                    # Save and return this error image
                    output_path = OUTPUT_DIR / f"{image_id}_error_output.png"
                    result.save(output_path)
                    
                    with open(output_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                    
                    return {
                        "success": False,
                        "message": f"Generation failed, created placeholder image: {error_msg}",
                        "url": f"/outputs/{output_path.name}",
                        "image_data_base64": f"data:image/png;base64,{encoded}",
                        "error": error_msg
                    }
                except Exception as final_error:
                    logger.error(f"Even placeholder creation failed: {final_error}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Image generation failed completely: {str(gen_error) or 'Unknown error'}"
                    )

        # Post-process for face similarity
        result = post_process_for_face_similarity(input_image, result, faces)

        # Save and return
        output_path = OUTPUT_DIR / f"{image_id}_output.png"
        result.save(output_path)

        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        return {
            "success": True,
            "message": "Image generated successfully",
            "url": f"/outputs/{output_path.name}",
            "image_data_base64": f"data:image/png;base64,{encoded}",
            "faces_detected": len(faces)
        }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Generation failed: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@app.post("/generate-with-lora")
async def generate_with_lora(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    model_id: str = Form(...),
    lora_id: str = Form(...),
    lora_scale: float = Form(0.8),
    strength: float = Form(0.45),
    guidance_scale: float = Form(8.0),
    steps: int = Form(50)
):
    """Generate image with LoRA emphasis"""
    try:
        # Log start of process
        logger.info(f"Starting image generation with LoRA emphasis using model: {model_id} and LoRA: {lora_id}")
        
        # Save input image
        content = await image.read()
        input_image = Image.open(io.BytesIO(content)).convert("RGB")
        image_id = uuid.uuid4().hex
        input_path = UPLOAD_DIR / f"{image_id}_input.png"
        input_image.save(input_path)
        
        # Translate prompt
        final_prompt = translate_prompt(prompt, Language.EN)
        
        # Load model
        model_path = MODEL_DIR / f"{model_id}.safetensors"
        if not model_path.exists():
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found.")
        
        pipe = load_pipeline(model_path)
        
        # Apply LoRA
        pipe = apply_lora(pipe, lora_id, lora_scale)
        
        # Generate image
        result = pipe(
            prompt=final_prompt,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=steps,
            output_type="pil"
        ).images[0]
        
        # Save and return
        output_path = OUTPUT_DIR / f"{image_id}_output.png"
        result.save(output_path)
        
        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        
        return {
            "success": True,
            "message": "Image generated successfully with LoRA emphasis",
            "url": f"/outputs/{output_path.name}",
            "image_data_base64": f"data:image/png;base64,{encoded}"
        }
    except Exception as e:
        logger.error(f"Generation with LoRA failed: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation with LoRA failed: {str(e)}")

@app.post("/simple-generate")
async def simple_generate(
    image: UploadFile = File(...),
    prompt: str = Form("Enhance this photo"),
):
    """Ultra-simplified image generation that should always work"""
    try:
        # Read input image
        content = await image.read()
        input_image = Image.open(io.BytesIO(content)).convert("RGB")
        image_id = uuid.uuid4().hex
        
        # Small size to avoid memory issues
        input_image = input_image.resize((256, 256), Image.LANCZOS)
        
        # Create a fake "enhanced" version by adjusting brightness and contrast
        enhanced = input_image.copy()
        
        # Apply some simple enhancements
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(1.2)  # Increase contrast
        enhancer = ImageEnhance.Brightness(enhanced)  
        enhanced = enhancer.enhance(1.1)  # Slightly brighter
        enhancer = ImageEnhance.Color(enhanced)
        enhanced = enhancer.enhance(1.3)  # More colorful
        enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = enhancer.enhance(1.5)  # Sharper
        
        # Add text based on prompt
        draw = ImageDraw.Draw(enhanced)
        draw.text((10, 10), f"Prompt: {prompt}", fill=(255, 255, 255))
        
        # Save and return
        output_path = OUTPUT_DIR / f"{image_id}_simple_output.png"
        enhanced.save(output_path)
        
        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "success": True,
            "message": "Image enhanced using fallback method",
            "url": f"/outputs/{output_path.name}",
            "image_data_base64": f"data:image/png;base64,{encoded}"
        }
        
    except Exception as e:
        logger.error(f"Simple generation failed: {e}")
        # Create an absolute minimal response
        img = Image.new('RGB', (256, 256), color=(100, 149, 237))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Error: " + str(e)[:50], fill=(255, 255, 255))
        
        output_path = OUTPUT_DIR / f"emergency_output.png"
        img.save(output_path)
        
        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "success": False,
            "message": f"Used emergency generator: {str(e)}",
            "image_data_base64": f"data:image/png;base64,{encoded}"
        }

@app.post("/face-preserving-generate")
async def face_preserving_generate(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    model_id: str = Form(...),
    face_fidelity: float = Form(0.9),  # Higher = more face preservation
    strength: float = Form(0.4),  # Lower = more reference preservation
    guidance_scale: float = Form(8.0),
    steps: int = Form(50),
    lora_id: Optional[str] = Form(None),
    lora_scale: float = Form(0.7),
    low_memory_mode: bool = Form(False)
):
    """Generate image with extreme face preservation while following the prompt"""
    try:
        # Check disk space and clean up if needed
        if not check_disk_space(OUTPUT_DIR, required_mb=50):
            # Try cleaning up older files first (keep very recent ones)
            cleanup_project_files(days_to_keep=0.5)  # Keep files from last 12 hours

            # If still not enough space, use emergency cleanup
            if not check_disk_space(OUTPUT_DIR, required_mb=20):
                emergency_cleanup()

        # Read input image
        content = await image.read()
        input_image = Image.open(io.BytesIO(content)).convert("RGB")
        image_id = uuid.uuid4().hex
        
        # Save input for reference
        input_path = UPLOAD_DIR / f"{image_id}_input.png"
        logger.info(f"Saving input image to {input_path}")
        input_image.save(input_path)
        logger.info("Input image saved successfully")
        
        # Construct a face-preserving prompt
        face_preserve_prompt = f"{prompt}, same face, exactly same person, same identity, perfect face, detailed facial features"
        logger.info(f"Using face-preserving prompt: {face_preserve_prompt}")
        
        # Detect faces with both OpenCV and enhanced detection
        logger.info("Detecting faces in input image...")
        try:
            faces = face_preserver.detect_faces(input_image)
            logger.info(f"Face detection complete. Found {len(faces)} faces.")
        except Exception as face_error:
            logger.error(f"Face detection failed: {face_error}")
            faces = []
            logger.info("Continuing without face detection")
        
        if len(faces) == 0:
            logger.warning("No faces detected with standard detector, continuing with lower strength for safety")
            # If no faces detected, still use lower strength to preserve important features
            strength = min(strength, 0.35)
        else:
            logger.info(f"Detected {len(faces)} faces, creating precision mask")
            
            # Create an enhanced precision face mask with larger padding
            face_mask = create_enhanced_face_mask(input_image, faces, padding=80, feather=30)
            
            # Set very low strength specifically for face areas
            strength = min(strength, 0.3)
            # Use more steps for higher quality
            steps = max(steps, 60)
        
        # For low memory mode, use smaller image dimensions
        if low_memory_mode:
            # Resize images to smaller dimensions to save memory
            input_image = input_image.resize((384, 384), Image.LANCZOS)
            steps = min(steps, 30)  # Reduce steps
            logger.info("Using low memory mode with reduced image size and steps")
        
        # Load model
        model_path = MODEL_DIR / f"{model_id}.safetensors"
        if not model_path.exists():
            available_models = [f.stem for f in MODEL_DIR.glob("*.safetensors")]
            raise HTTPException(status_code=404, 
                detail=f"Model '{model_id}' not found. Available models: {available_models}")
        
        pipe = load_pipeline(model_path)
        
        # Apply LoRA if specified
        if lora_id:
            pipe = apply_lora(pipe, lora_id, lora_scale)
        
        # Process based on pipeline type
        is_xl_pipeline = isinstance(pipe, StableDiffusionXLImg2ImgPipeline)
        
        if len(faces) > 0 and not is_xl_pipeline:
            # For standard SD with faces, use inpainting for precision control
            from diffusers import StableDiffusionInpaintPipeline
            
            try:
                # Convert to inpainting pipeline
                components = pipe.components
                inpaint_pipe = StableDiffusionInpaintPipeline(**components)
                inpaint_pipe.to("cpu")
                
                # Use inpainting with mask
                result = inpaint_pipe(
                    prompt=face_preserve_prompt,
                    negative_prompt="deformed face, blurry face, distorted face, disfigured",
                    image=input_image,
                    mask_image=face_mask,
                    strength=strength,
                    guidance_scale=guidance_scale,
                    num_inference_steps=steps
                ).images[0]
                
            except Exception as e:
                logger.warning(f"Inpainting failed: {e}, falling back to regular img2img")
                result = pipe(
                    prompt=face_preserve_prompt,
                    negative_prompt="deformed face, blurry face, distorted face, disfigured",
                    image=input_image,
                    strength=strength,
                    guidance_scale=guidance_scale,
                    num_inference_steps=steps
                ).images[0]
        else:
            # For SDXL or no faces detected, use regular img2img with careful settings
            result = pipe(
                prompt=face_preserve_prompt,
                negative_prompt="deformed face, blurry face, distorted face, disfigured",
                image=input_image,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=steps
            ).images[0]
        
        # Post-process for face similarity
        result = post_process_for_face_similarity(input_image, result, faces, face_fidelity)

        # Save and return
        output_path = OUTPUT_DIR / f"{image_id}_face_preserved_output.png"
        result.save(output_path)
        
        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "success": True,
            "message": "Image generated with face preservation",
            "url": f"/outputs/{output_path.name}",
            "image_data_base64": f"data:image/png;base64,{encoded}",
            "faces_detected": len(faces)
        }
        
    except Exception as e:
        error_message = get_error_message(e)
        logger.error(f"Face-preserving generation failed: {error_message}")
        raise HTTPException(status_code=500, detail=f"Face-preserving generation failed: {error_message}")

@app.post("/test-face-preserve")
async def test_face_preserve(
    image: UploadFile = File(...),
    prompt: str = Form("Enhance this photo"),
):
    """Simplified face-preserving generation for testing"""
    try:
        # Read input image
        content = await image.read()
        input_image = Image.open(io.BytesIO(content)).convert("RGB")
        image_id = uuid.uuid4().hex
        
        # Detect faces
        faces = face_preserver.detect_faces(input_image)
        
        # Create a basic enhanced version  
        enhanced = enhance_image_quality(input_image)
        
        # Save and return
        output_path = OUTPUT_DIR / f"{image_id}_test_output.png"
        enhanced.save(output_path)
        
        with open(output_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        return {
            "success": True,
            "message": f"Test successful. Found {len(faces)} faces.",
            "image_data_base64": f"data:image/png;base64,{encoded}" 
        }
    except Exception as e:
        import traceback
        logger.error(f"Test failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@app.get("/outputs/{filename}")
def get_output(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

@app.get("/models")
def list_models():
    return [f.name for f in MODEL_DIR.glob("*.safetensors")]

@app.get("/loras")
def list_loras():
    """List all available LoRA files"""
    lora_files = []
    for ext in [".safetensors", ".pt"]:
        files = list(LORA_DIR.glob(f"*{ext}"))
        for f in files:
            lora_files.append({
                "id": f.stem,
                "name": f.stem.replace("_", " ").title(),
                "path": str(f),
                "size_mb": round(f.stat().st_size / (1024*1024), 2)
            })
    
    return {"loras": lora_files}

@app.get("/health")
def health():
    return {"status": "ok", "models_available": list_models()}

@app.get("/debug")
def debug_info():
    """Return detailed debugging information"""
    models_dir = MODEL_DIR
    
    # Check model directory
    models_exist = models_dir.exists()
    model_files = list(models_dir.glob("*.safetensors")) if models_exist else []
    model_sizes = {f.name: f.stat().st_size / (1024**3) for f in model_files} if model_files else {}
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    cuda_device = torch.cuda.get_device_name(0) if cuda_available else "N/A"
    
    # Check modules
    has_diffusers = "diffusers" in sys.modules
    has_transformers = "transformers" in sys.modules
    
    # Check environment
    env_vars = {
        "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
    }
    
    actual_models = []
    for ext in [".safetensors", ".ckpt", ".bin", ".pt"]:
        files = list(MODEL_DIR.glob(f"*{ext}"))
        for f in files:
            actual_models.append({
                "name": f.name,
                "path": str(f),
                "size_mb": f.stat().st_size / (1024*1024)
            })
    
    return {
        "system": {
            "python_version": sys.version,
            "torch_version": torch.__version__,
            "cuda_available": cuda_available,
            "cuda_device": cuda_device,
            "working_directory": str(Path.cwd())
        },
        "models": {
            "directory_exists": models_exist,
            "model_count": len(model_files),
            "model_files": [f.name for f in model_files],
            "model_sizes_gb": model_sizes,
            "actual_models": actual_models
        },
        "modules": {
            "diffusers_available": has_diffusers,
            "transformers_available": has_transformers,
        },
        "environment": env_vars
    }

@app.get("/test-model/{model_id}")
def test_model_loading(model_id: str):
    """Test loading a model without generating an image"""
    try:
        model_path = MODEL_DIR / f"{model_id}.safetensors"
        if not model_path.exists():  
            available_models = [f.stem for f in MODEL_DIR.glob("*.safetensors")]
            return {
                "success": False,
                "error": f"Model not found: {model_id}",
                "available_models": available_models
            }
        
        # Try loading the model
        pipe = load_pipeline(model_path)
        return {"success": True, "message": f"Model {model_id} loaded successfully"}
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("img2img:app", host="0.0.0.0", port=8000, reload=True)
