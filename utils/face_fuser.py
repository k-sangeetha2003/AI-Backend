import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
import os

# Increase detection size and lower threshold for more accurate detection
app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.4)

# Make sure you're using the right model for swapping
INSWAPPER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "insightface", "inswapper_128.onnx")
swapper = insightface.model_zoo.get_model(INSWAPPER_PATH)

def exact_face_swap(source_img_path, target_img_path, output_path):
    """
    Perform exact face swapping from source to target
    
    Args:
        source_img_path: Path to image with source faces
        target_img_path: Path to target image
        output_path: Path to save the result
    """
    # Load images
    source_img = cv2.imread(source_img_path)
    target_img = cv2.imread(target_img_path)
    
    if source_img is None or target_img is None:
        print("Error loading images")
        return None
        
    # Get faces
    source_faces = app.get(source_img)
    target_faces = app.get(target_img)
    
    if len(source_faces) == 0:
        print("No faces found in source image")
        return None
    
    if len(target_faces) == 0:
        print("No faces found in target image")
        return None
    
    print(f"Found {len(source_faces)} faces in source and {len(target_faces)} faces in target")
    
    # Match faces by position in couples (typically left-right)
    if len(source_faces) == 2 and len(target_faces) == 2:
        # Sort by x position (left to right)
        source_faces.sort(key=lambda x: x.bbox[0])
        target_faces.sort(key=lambda x: x.bbox[0])
    
    # Process result
    result = target_img.copy()
    
    # Swap faces one by one with exact replacement
    for i, target_face in enumerate(target_faces):
        # Get corresponding source face (cycle if needed)
        source_idx = min(i, len(source_faces) - 1)
        source_face = source_faces[source_idx]
        
        # Apply face swap with enhanced settings
        result = swapper.get(
            result,              # image
            target_face,         # detected face in target
            source_face,         # source face
            paste_back=True,     # paste the face back to image
        )
    
    # Save result
    cv2.imwrite(output_path, result)
    return output_path

def face_swap(source_pil, target_pil, max_faces=3):
    # ...function implementation...
    pass

def multi_face_swap_with_reference(*args, **kwargs):
    # TODO: Implement this function
    pass
