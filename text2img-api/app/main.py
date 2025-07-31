from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from app.config import settings
from app.api import generation, models, sessions, files

# Create FastAPI app
app = FastAPI(
    title="Text-to-Image Generation API",
    description="Generate high-quality, photorealistic images from text prompts.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for generated images
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Include API routes
app.include_router(generation.router, prefix="/api/v1", tags=["generation"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Text-to-Image Generation API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
