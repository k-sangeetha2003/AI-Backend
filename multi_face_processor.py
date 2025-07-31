import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import cv2
import numpy as np
import os
from typing import List, Dict, Any, Tuple
from utils.face_fuser import app as face_app, swapper

# Define the face type more explicitly since it was imported
Face = Dict[str, Any]
VisionFrame = np.ndarray

_reference_faces: List[Face] = []

def get_reference_faces() -> List[Face]:
    global _reference_faces
    return _reference_faces

def set_reference_faces(faces: List[Face]) -> None:
    global _reference_faces
    _reference_faces = faces

def get_analysed_faces(frame: np.ndarray) -> List[Face]:
    """Helper to analyze faces in a frame"""
    faces = face_app.get(frame)
    # Sort faces by size (largest first) for consistent processing
    if faces:
        faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
    return faces

def read_image(image_path: str) -> np.ndarray:
    """Helper to read an image"""
    return cv2.imread(image_path)

def write_image(image_path: str, frame: np.ndarray) -> None:
    """Helper to write an image"""
    cv2.imwrite(image_path, frame)

def analyze_reference_image(image_path: str) -> Tuple[int, List[Face]]:
    """
    Analyze reference image to determine number of faces
    Returns: tuple of (face count, face objects)
    """
    image = read_image(image_path)
    if image is None:
        return 0, []
        
    faces = get_analysed_faces(image)
    return len(faces), faces

class MultiFaceProcessor:
    def __init__(self):
        self.gender_filter = None  # 'female', 'male', or None
        self.num_faces = 0
        self.reference_faces = []
        self.target_faces = []
        self.auto_detect_faces = True
        self.exact_swap = True  # Enable exact face swap by default
    
    def set_options(self, gender=None, num_faces=0, auto_detect=True, exact_swap=True):
        """
        Set options for face processing
        If auto_detect is True, num_faces is used as a maximum limit
        """
        self.gender_filter = gender
        self.num_faces = num_faces
        self.auto_detect_faces = auto_detect
        self.exact_swap = exact_swap
    
    def get_reference_face(self, source_path):
        """Load reference face(s) from source"""
        if os.path.isfile(source_path):
            source_frame = read_image(source_path)
            if source_frame is not None:
                faces = get_analysed_faces(source_frame)
                self.reference_faces = faces
                if self.auto_detect_faces:
                    # Auto-set the number of faces based on detection
                    self.num_faces = len(faces)
                    print(f"Auto-detected {self.num_faces} faces in reference image")
                return faces
        return []
    
    def process_frame(self, frame: VisionFrame) -> VisionFrame:
        """Process frame with exact face swap"""
        # Detect faces in the target frame
        target_faces = get_analysed_faces(frame)
        
        if not target_faces or len(target_faces) == 0:
            print("No faces detected in target image")
            return frame
        
        # Use detected number of faces from reference if auto_detect is on
        face_limit = self.num_faces if self.num_faces > 0 else len(target_faces)
        
        # Limit to specified number of faces
        target_faces = target_faces[:face_limit]
        
        # Get reference faces (face to swap with)
        reference_faces = self.reference_faces if self.reference_faces else get_reference_faces()
        
        if not reference_faces:
            print("No reference faces available")
            return frame
        
        # Match faces for couple photos (left-right order)
        if len(reference_faces) == 2 and len(target_faces) == 2:
            # Sort by horizontal position
            reference_faces.sort(key=lambda x: x.bbox[0])
            target_faces.sort(key=lambda x: x.bbox[0])
        
        # Process each detected face
        result_frame = frame.copy()
        for i, target_face in enumerate(target_faces):
            # Get corresponding reference face (cycle through if needed)
            ref_idx = i % len(reference_faces)
            ref_face = reference_faces[ref_idx]
            
            # Apply face swap with exact replacement
            try:
                # For exact swap, we use more aggressive settings
                result_frame = swapper.get(
                    result_frame,     # image
                    target_face,      # detected face in target
                    ref_face,         # source face
                    paste_back=True   # paste the face back to image
                )
                print(f"Swapped face {i+1} successfully")
            except Exception as e:
                print(f"Error swapping face {i+1}: {e}")
        
        return result_frame
    
    def swap_exact(self, source_path: str, target_path: str, output_path: str) -> str:
        """
        Perform complete face swap from source to target
        
        Args:
            source_path: Path to source image with reference faces
            target_path: Path to target image
            output_path: Path to save the result
        """
        # Get reference faces
        self.get_reference_face(source_path)
        
        # Load target image
        target_img = read_image(target_path)
        if target_img is None:
            return None
        
        # Apply face swap
        result = self.process_frame(target_img)
        
        # Save result
        write_image(output_path, result)
        return output_path
    
def count_genders(faces):
    """
    Count number of men and women in a list of faces.
    Returns: (num_men, num_women)
    """
    num_men = 0
    num_women = 0
    for face in faces:
        # insightface: 0 = female, 1 = male
        gender = face.get('gender') if isinstance(face, dict) else getattr(face, 'gender', None)
        if gender == 1:
            num_men += 1
        elif gender == 0:
            num_women += 1
    return num_men, num_women