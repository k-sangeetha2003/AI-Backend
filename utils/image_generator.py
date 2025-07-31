from PIL import Image
import os
import uuid
import time
from utils.face_fuser import face_swap
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
import torch
import cv2
import numpy as np
import random
from insightface.app import FaceAnalysis  
from fastapi import Form
from multi_face_processor import analyze_reference_image, MultiFaceProcessor
  
# More robust device detection
def get_optimal_device():
    if torch.cuda.is_available():
        print("CUDA GPU detected - using GPU acceleration")
        return "cuda"
    else:
        print("No GPU detected - using CPU mode (will be slower)")
        return "cpu"

device = get_optimal_device()

# Set environment variables to optimize for CPU if needed
if device == "cpu":
    os.environ['OMP_NUM_THREADS'] = '4'  # Optimize OpenMP threading
    torch.set_num_threads(4)  # Limit PyTorch CPU threads to prevent overloading

def enhance_prompt_for_portrait(prompt):
    """Add details to ensure full-body portrait generation"""
    portrait_terms = [
        "full body portrait",
        "full-length portrait", 
        "standing full body",
        "full figure portrait"
    ]
    quality_terms = [
        "8k resolution, highly detailed",
        "professional studio lighting, sharp focus",
        "intricate details, masterpiece, perfect composition"
    ]
    
    enhanced_prompt = f"{prompt}, {random.choice(portrait_terms)}, {random.choice(quality_terms)}"
    return enhanced_prompt

def detect_face_count(image_path):
    """
    Detect how many faces are in the reference image
    Returns: number of faces detected
    """
    count, _ = analyze_reference_image(image_path)
    return count

def generate_image_with_facefusion(prompt, input_path, model_path, lora_path=None, 
                                 portrait_mode=True, negative_prompt=None, 
                                 guidance_scale=7.5, num_steps=40,
                                 sampler="DPM++ 2M Karras", upscale=True, 
                                 face_restore=True, denoising_strength=0.7, clip_skip=1,
                                 width=None, height=None, multi_face=True, max_faces=0, output_path=None):
    """Enhanced image generation with auto face-count detection"""
    # First, detect how many faces are in the reference image
    detected_face_count = detect_face_count(input_path)
    
    # Use detected count unless max_faces override is provided
    faces_to_process = detected_face_count if max_faces == 0 else min(detected_face_count, max_faces)
    
    print(f"Detected {detected_face_count} faces in reference image, will process {faces_to_process}")
    
    # Adjust prompt based on number of faces
    if detected_face_count == 2:
        # Couple-specific prompting
        prompt = f"{prompt}, couple, two people together"
    elif detected_face_count > 2:
        # Group-specific prompting
        prompt = f"{prompt}, group of {detected_face_count} people together"
    
    # Enhanced prompting for quality
    quality_boost_terms = "masterpiece, best quality, extremely detailed, 8k uhd, high resolution, photorealistic, professional photography"
    prompt = f"{prompt}, {quality_boost_terms}"
    
    # Improved negative prompt with quality-reducing terms
    base_negative = "deformed, distorted, disfigured, poor details, bad anatomy, low quality, blurry, old, outdated"
    negative_prompt = f"{negative_prompt if negative_prompt else ''}, {base_negative}"
    
      # 4K resolution settings
    if width is None or height is None:
        # Use intermediate resolution for initial generation to avoid memory issues
        if portrait_mode:
            # Portrait 4K aspect ratio (9:16 approximate)
            height = 1536  # Initial generation at moderate resolution
            width = 864
        else:
            # Landscape 4K aspect ratio (16:9)
            width = 1536
            height = 864
    
    # Final 4K target dimensions for upscaling
    if portrait_mode:
        target_width = 2160
        target_height = 3840  # 4K portrait (9:16)
    else:
        target_width = 3840
        target_height = 2160  # 4K landscape (16:9)
    
    # Load source image
    source_img = cv2.imread(input_path)
    
    # Resize maintaining aspect ratio to fit within target dimensions
    h, w = source_img.shape[:2]
    scaling = min(width/w, height/h)
    new_size = (int(w*scaling), int(h*scaling))
    resized_img = cv2.resize(source_img, new_size)
    
    # Create canvas with proper portrait dimensions
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    y_offset = (height - new_size[1]) // 2
    x_offset = (width - new_size[0]) // 2
    canvas[y_offset:y_offset+new_size[1], x_offset:x_offset+new_size[0]] = resized_img
    
    # Convert to PIL for diffusers
    source_pil = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
    
    # Memory optimization
    if device == "cuda":
        torch.cuda.empty_cache()
    import gc
    gc.collect()
    
    # Default LoRA for portrait enhancement if none provided
    if lora_path is None:
        # Look for portrait enhancement LoRAs in the loras directory
        loras_dir = os.path.join("models", "loras")
        portrait_loras = [os.path.join(loras_dir, f) for f in os.listdir(loras_dir) 
                         if any(term in f.lower() for term in 
                               ["portrait", "photorealistic", "detail", "quality"])]
        if portrait_loras:
            lora_path = portrait_loras[0]  # Use the first matching LoRA
            print(f"Using default portrait enhancement LoRA: {os.path.basename(lora_path)}")
    
    # Detect if model is SDXL based on filename or size
    is_xl_model = "xl" in model_path.lower() or "sdxl" in model_path.lower()
    
    # Load appropriate pipeline based on model type
    model_dtype = torch.float16 if device == "cuda" else torch.float32
    print(f"Loading model {os.path.basename(model_path)} with dtype {model_dtype}")
    
    if is_xl_model:
        from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
        pipe = StableDiffusionXLPipeline.from_single_file(
            model_path,
            torch_dtype=model_dtype,
            safety_checker=None
        ).to(device)
    else:
        pipe = StableDiffusionPipeline.from_single_file(
            model_path,
            torch_dtype=model_dtype,
            safety_checker=None
        ).to(device)
    
    # Optimize for CPU
    if device == "cpu":
        print("Applying CPU optimizations for high-quality generation")
        pipe.enable_attention_slicing(slice_size="max")
        if not is_xl_model:  # CPU optimization only applicable to non-XL models
            torch.backends.cuda.matmul.allow_tf32 = True
    else:
        print("Applying GPU optimizations")
    
    # Load LoRA if provided
    if lora_path and os.path.exists(lora_path):
        try:
            adapter_name = os.path.basename(lora_path).split(".")[0]
            pipe.load_lora_weights(
                pretrained_model_name_or_path=os.path.dirname(lora_path),
                weight_name=os.path.basename(lora_path),
                adapter_name=adapter_name,
                local_files_only=True
            )
            pipe.set_adapters([adapter_name], adapter_weights=[0.7])  # 0.7 weight for balanced effect
        except Exception as e:
            print(f"Error loading LoRA with newer method: {e}")
            try:
                # Fallback for other versions
                from safetensors.torch import load_file
                state_dict = load_file(lora_path)
                pipe.unet.load_attn_procs(state_dict)
            except Exception as e2:
                print(f"Error loading LoRA with fallback method: {e2}")
    
    # Generate the image with appropriate pipeline
    try:
        if is_xl_model:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_steps,
                width=width,
                height=height,
            )
        else:
            result = pipe(
                prompt=prompt, 
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=num_steps,
                width=width, 
                height=height,
            )
        
        gen_image = result.images[0]
        
        # Apply face fusion with auto-detected faces
        processor = MultiFaceProcessor()
        processor.set_options(num_faces=faces_to_process, auto_detect=True)
        processor.get_reference_face(input_path)
        
        # Process generated image with face swapping
        # Use processor to swap faces in the generated image
        # Convert PIL image to OpenCV format for processing
        gen_image_cv = cv2.cvtColor(np.array(gen_image), cv2.COLOR_RGB2BGR)
        result_image = processor.swap_faces(gen_image_cv)
        
        # Save the image
        if result_image is None:
            print("Image generation failed: result_image is None")
            return None
        cv2.imwrite(output_path, result_image)
        if os.path.exists(output_path):
            return output_path
        else:
            print("Failed to save image at:", output_path)
            return None
    except Exception as e:
        print(f"Error during high-quality generation: {e}")
        # Fallback: ensure fused is defined or handle gracefully
        fused = None
        # Try again with lower resolution
        fallback_width = width // 1.5 if width > 640 else width
        fallback_height = height // 1.5 if height > 640 else height
        
        if is_xl_model:
            result = pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale,
                num_inference_steps=min(num_steps, 30),
                width=fallback_width,
                height=fallback_height,
            )
        else:
            result = pipe(
                prompt=prompt, 
                negative_prompt=negative_prompt,
                guidance_scale=guidance_scale, 
                num_inference_steps=min(num_steps, 30),
                width=fallback_width,
                height=fallback_height,
            )
            
        gen_image = result.images[0]
        fused = face_swap(source_pil, gen_image)
        output_path = os.path.join("outputs", f"fallback_{uuid.uuid4().hex}.png")
        fused.save(output_path)
        return output_path
def detect_best_face(image):
    """Detect the most prominent face with CPU/GPU compatibility"""
    app = FaceAnalysis(name='buffalo_l')
    
    # Use ctx_id=-1 for CPU, 0 for GPU
    ctx_id = 0 if device == "cuda" else -1
    
    # Adjust detection size based on available compute resources
    det_size = (640, 640) if device == "cuda" else (320, 320)
    
    app.prepare(ctx_id=ctx_id, det_size=det_size)
    
    # Get faces with InsightFace
    faces = app.get(image)
    
    # Sort by face size (area of bounding box)
    if len(faces) > 0:
        faces = sorted(faces, key=lambda x: 
                     (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), 
                     reverse=True)
        return faces
    return []

def blend_face(source_face, target_image, face_mask):
    # Apply Poisson blending for seamless integration
    center = (int((face_mask[1] + face_mask[3]) / 2), 
             int((face_mask[0] + face_mask[2]) / 2))
    output = cv2.seamlessClone(
        source_face, target_image, 
        cv2.cvtColor(np.ones(source_face.shape, dtype=np.uint8) * 255, cv2.COLOR_BGR2GRAY),
        center, cv2.NORMAL_CLONE
    )
    return output

torch.cuda.empty_cache()

def process_couple_image(source_img, target_img, gender_balance=True):
    """
    Specialized processing for couple images
    
    Args:
        source_img: Path to image containing source faces
        target_img: Path to target image
        gender_balance: Try to match faces by apparent gender
    """
    source = cv2.imread(source_img)
    target = cv2.imread(target_img)
    
    if source is None or target is None:
        print("Error loading images")
        return None
        
    # Use specialized couple detection
    from utils.face_fuser import detect_couple_faces, swapper
    
    source_faces = detect_couple_faces(source)
    target_faces = detect_couple_faces(target)
    
    if len(source_faces) != 2 or len(target_faces) != 2:
        print(f"Warning: Expected 2 faces. Found {len(source_faces)} in source and {len(target_faces)} in target.")
        # Fall back to regular processing if exactly 2 faces aren't found
        
    result = target.copy()
    
    # Process each face with enhanced settings
    for i, target_face in enumerate(target_faces):
        source_idx = i
        if gender_balance and len(source_faces) == 2 and len(target_faces) == 2:
            # Try to match female/male pairs if possible
            # This is a simple heuristic - face width/height ratio differs slightly by gender
            # A more accurate approach would use a gender classifier
            source_ratio = (source_faces[0].bbox[2] - source_faces[0].bbox[0]) / (source_faces[0].bbox[3] - source_faces[0].bbox[1])
            source_ratio2 = (source_faces[1].bbox[2] - source_faces[1].bbox[0]) / (source_faces[1].bbox[3] - source_faces[1].bbox[1])
            target_ratio = (target_face.bbox[2] - target_face.bbox[0]) / (target_face.bbox[3] - target_face.bbox[1])
            
            # Closer ratio suggests same gender
            if abs(source_ratio - target_ratio) > abs(source_ratio2 - target_ratio):
                source_idx = 1
                
        # Apply face swap with enhanced settings
        try:
            result = swapper.get(result, target_face, source_faces[source_idx], paste_back=True)
        except Exception as e:
            print(f"Error processing face {i+1}: {e}")
    
    return result

def generate_image_with_exact_swap(prompt, input_path, model_path, output_path=None, lora_path=None,
                                  negative_prompt=None, guidance_scale=7.5, num_steps=40, 
                                  width=768, height=768):
    """
    Generate an image with exact face swapping from reference
    """
    # Your existing generation code to create the base image
    # ...
    
    # After generation, apply exact face swap
    from multi_face_processor import MultiFaceProcessor
    
    processor = MultiFaceProcessor()
    processor.set_options(exact_swap=True)
    
    # Use temporary paths if needed
    if output_path is None:
        output_path = os.path.join("outputs", f"exact_swap_{int(time.time())}.png")
    
    # Path to the generated image before face swapping
    temp_generated_path = output_path.replace(".png", "_before_swap.png")
    
    # Apply exact face swap
    final_path = processor.swap_exact(
        source_path=input_path,
        target_path=temp_generated_path,  # Your generated image path
        output_path=output_path
    )
    
    return final_path
