from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import os
import shutil
from utils.image_generator import generate_image_with_facefusion, generate_image_with_exact_swap
from multi_face_processor import analyze_reference_image, count_genders
import time

app = FastAPI(title="Face Fusion API")

MODELS_DIR = "models"
BASE_MODELS_DIR = os.path.join(MODELS_DIR, "base")
INPUTS_DIR = "inputs"
OUTPUTS_DIR = "outputs"

os.makedirs(INPUTS_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)

@app.get("/models/", response_model=List[str])
def get_models():
    if not os.path.exists(BASE_MODELS_DIR):
        return []
    return [f for f in os.listdir(BASE_MODELS_DIR) if f.endswith(".safetensors")]

@app.get("/loras/", response_model=List[str])
def get_loras():
    loras_path = os.path.join(MODELS_DIR, "loras")
    return [f for f in os.listdir(loras_path) if f.endswith(".safetensors")]

@app.post("/generate/")
async def generate_image(
    prompt: str = Form(...),
    image: UploadFile = File(...),
    model_name: str = Form(...),
    lora_name: str = Form(None),
    negative_prompt: str = Form("deformed, distorted, disfigured, poor details, bad anatomy, low quality"),
    portrait_mode: bool = Form(True),
    guidance_scale: float = Form(7.5),
    num_steps: int = Form(40),
    width: int = Form(512),
    height: int = Form(768),
    multi_face: bool = Form(True),
    max_faces: int = Form(0),
    exact_face_swap: bool = Form(False, description="Enable exact face swap mode (optional)")
):
    print("prompt:", prompt)
    print("image:", image)
    print("model_name:", model_name)
    # Save input image
    input_path = os.path.join(INPUTS_DIR, image.filename)
    with open(input_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # Use input image as reference image
    ref_path = input_path

    # Face and gender analysis
    face_count, ref_faces = analyze_reference_image(ref_path)
    if face_count > 0:
        prompt += f", {face_count} people"

    num_men, num_women = count_genders(ref_faces)
    gender_str = []
    if num_women:
        gender_str.append(f"{num_women} woman{'s' if num_women > 1 else ''}")
    if num_men:
        gender_str.append(f"{num_men} man{'s' if num_men > 1 else ''}")
    if gender_str:
        prompt += f", generate a scene with {' and '.join(gender_str)}"

    # Couple/group prompt enhancement
    if face_count == 2:
        prompt += ", romantic couple, detailed faces, emotional connection, sharp features"
    elif face_count > 2:
        prompt += f", group of {face_count} people, group photo, multiple people, perfect faces, sharp features, high detail"

    model_path = os.path.join(BASE_MODELS_DIR, model_name)
    lora_path = os.path.join(MODELS_DIR, "loras", lora_name) if lora_name else None

    # Output path
    timestamp = int(time.time())
    output_path = os.path.join(OUTPUTS_DIR, f"generated_{timestamp}.png")

    # Choose generation method
    if exact_face_swap:
        final_path = generate_image_with_exact_swap(
            prompt=prompt,
            input_path=input_path,
            model_path=model_path,
            output_path=output_path,
            lora_path=lora_path,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            num_steps=num_steps,
            width=width,
            height=height
        )
    else:
        final_path = generate_image_with_facefusion(
            prompt=prompt,
            input_path=input_path,
            model_path=model_path,
            lora_path=lora_path,
            portrait_mode=portrait_mode,
            negative_prompt=negative_prompt,
            guidance_scale=guidance_scale,
            num_steps=num_steps,
            width=width,
            height=height,
            multi_face=multi_face,
            max_faces=max_faces,
        )

    print("Final path:", final_path)
    if not final_path or not isinstance(final_path, str) or not os.path.exists(final_path):
        return JSONResponse(
            status_code=500,
            content={"error": "Output image not found. Check if the image was generated successfully."}
        )
    return FileResponse(final_path, media_type="image/png", filename=os.path.basename(final_path))
