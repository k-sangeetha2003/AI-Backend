@app.post("/face-preserving-generate")
async def face_preserving_generate(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    model_id: str = Form(...),
    strength: float = Form(0.2),  # Lower = more preservation
    guidance_scale: float = Form(8.0),
    steps: int = Form(50),
    lora_id: Optional[str] = Form(None),
    lora_scale: float = Form(0.7)
):
    # Read input image
    content = await image.read()
    input_image = Image.open(io.BytesIO(content)).convert("RGB")
    image_id = uuid.uuid4().hex

    # Detect faces
    faces = face_preserver.detect_faces(input_image)

    # Create face mask if faces found
    face_mask = None
    if len(faces) > 0:
        face_mask = create_enhanced_face_mask(input_image, faces, padding=80, feather=30)

    # Load model and apply LoRA if needed
    model_path = MODEL_DIR / f"{model_id}.safetensors"
    pipe = load_pipeline(model_path)
    if lora_id:
        pipe = apply_lora(pipe, lora_id, lora_scale)

    # Use inpainting if possible, otherwise fallback to img2img
    if face_mask is not None:
        from diffusers import StableDiffusionInpaintPipeline
        inpaint_pipe = StableDiffusionInpaintPipeline(**pipe.components)
        inpaint_pipe.to("cpu")
        result = inpaint_pipe(
            prompt=prompt,
            negative_prompt="deformed face, blurry face, distorted face, disfigured",
            image=input_image,
            mask_image=face_mask,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=steps
        ).images[0]
    else:
        result = pipe(
            prompt=prompt,
            negative_prompt="deformed face, blurry face, distorted face, disfigured",
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=steps
        ).images[0]

    # Post-process for face similarity
    result = post_process_for_face_similarity(input_image, result, faces, face_fidelity=0.95)

    # Save and return result as before...