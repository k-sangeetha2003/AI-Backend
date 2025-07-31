# Mirage AI: Advanced Image Transformation API

Mirage AI is a powerful image-to-image transformation API built with FastAPI and Stable Diffusion models. The system allows users to transform images using text prompts in multiple languages with advanced features like face preservation, artistic styling, and LoRA (Low-Rank Adaptation) model customization.

## Features

- **Multi-language Support**: Process images with prompts in English, Spanish, French, German, and Italian
- **Advanced Face Preservation**: Preserve facial features during image transformation with multiple preservation levels
- **Artistic Style Transformations**: Apply various artistic styles like oil painting, watercolor, pencil sketching, anime, etc.
- **LoRA Support**: Use custom LoRA models to customize the style of generated images
- **Model Management**: Load, unload, and switch between different Stable Diffusion models
- **Conversation Tracking**: Track and manage image generation sessions with conversation history
- **Optimized Performance**: Automatic strength adjustment, memory management, and offline mode support

## Installation

### Prerequisites

- Python 3.8+
- CUDA-compatible GPU (recommended for optimal performance)
- 8+ GB VRAM for SDXL models, 4+ GB VRAM for SD 1.5 models

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/mirage-ai-project.git
   cd mirage-ai-project
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Linux/Mac
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the project directories:
   ```bash
   # Create required directories
   mkdir -p models loras outputs conversations data/raw
   ```

5. Add models to the `models` directory:
   - Place Stable Diffusion models (`.safetensors` files) in the `models` directory
   - Place LoRA models in the `loras` directory

## Project Structure

```
mirage-ai-project/
├── api/                # API implementation
├── data/               # Data storage
│   └── raw/            # Raw data files
├── docs/               # Documentation
├── mirage_ai/          # Core Python package
│   ├── __init__.py
│   └── ...
├── models/             # Stable Diffusion model files
├── loras/              # LoRA model files
├── outputs/            # Generated images
├── scripts/            # Utility scripts
├── tests/              # Test files
│   └── __init__.py
├── base_models/        # Base models for fallbacks
├── conversations/      # Stored conversation history
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## Usage

### Starting the Server

```bash
uvicorn i2i_all:app --host 0.0.0.0 --port 8000 --reload
```

### Basic Image Transformation

```python
import requests

url = "http://localhost:8000/img2img/"

# Parameters
files = {"image": open("input.jpg", "rb")}
data = {
    "prompt": "Make it look like a professional photograph",
    "language": "en",
    "strength": 0.8,
    "guidance_scale": 7.5,
    "preserve_faces": True
}

# Send request
response = requests.post(url, files=files, data=data)
print(response.json())
```

### Applying Artistic Styles

```python
import requests

url = "http://localhost:8000/artistic-img2img/"

files = {"image": open("portrait.jpg", "rb")}
data = {
    "style": "oil",  # oil, watercolor, pencil, acrylic, ghibli, anime, comic, pixar
    "preserve_level": "high",
    "strength": 0.65,
    "additional_prompt": "vibrant colors, detailed"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

## API Endpoints

### Image Transformation

- `POST /img2img/`: Transform an image using a text prompt
- `POST /img2img/{language}`: Transform with a specific language prompt
- `POST /simple-img2img/`: Simplified image transformation with automatic parameters
- `POST /face-preserving-img2img/`: Transform while preserving faces
- `POST /artistic-img2img/`: Apply artistic styles to images
- `POST /lora-with-face-preservation/`: Apply LoRA while preserving faces

### Model Management

- `GET /models/`: List all available models
- `GET /models/{model_id}`: Get information about a specific model
- `POST /models/{model_id}/load`: Load a specific model
- `POST /models/unload`: Unload models to free memory

### LoRA Management

- `GET /loras/`: List all available LoRAs
- `GET /loras/{lora_id}`: Get information about a specific LoRA
- `GET /models/{model_id}/compatible-loras`: Get LoRAs compatible with a model

### System Information

- `GET /system/info`: Get system information
- `GET /system/memory`: Get memory usage information
- `GET /system/loaded-models`: Get information about loaded models
- `GET /health`: Health check with status information

## Configuration

### Environment Variables

- `TF_CPP_MIN_LOG_LEVEL`: Control TensorFlow warning levels (0=all, 1=INFO, 2=WARNING, 3=ERROR)
- `HF_DATASETS_OFFLINE`: Set to "1" for offline mode
- `TRANSFORMERS_OFFLINE`: Set to "1" for offline mode
- `HF_HUB_OFFLINE`: Set to "1" for offline mode

### Directory Structure

- `models/`: Place Stable Diffusion models here (safetensors format)
- `loras/`: Place LoRA models here
- `base_models/`: Used for fallback text encoders
- `outputs/`: Generated images are saved here

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**: Reduce model size or batch size
   ```
   # Try unloading unused models
   requests.post("http://localhost:8000/models/unload")
   ```

2. **Model Loading Fails**: Ensure model files are compatible and correctly placed
   ```
   # Check model compatibility
   requests.get("http://localhost:8000/models/")
   ```

3. **LoRA Compatibility Issues**: Use force_lora parameter or check compatibility
   ```
   # Check LoRA compatibility
   requests.get("http://localhost:8000/check-compatibility/?model_id=model_name&lora_id=lora_name")
   ```

## License

[Specify your license information here]

## Credits

Mirage AI uses the following open-source projects:
- FastAPI
- Diffusers
- Transformers
- PyTorch
- Pillow
- OpenCV

## Contact

For support or inquiries, please contact [your contact information]
