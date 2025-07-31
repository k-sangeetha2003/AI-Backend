import os
import shutil
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

def ensure_directory(path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    """
    try:
        return Path(file_path).stat().st_size
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {e}")
        return 0

def format_file_size(size_bytes: int) -> str:
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

def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
    """
    Clean up old files in directory.
    """
    try:
        import time
        current_time = time.time()
        deleted_count = 0
        
        for file_path in Path(directory).glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > (max_age_days * 24 * 60 * 60):
                    file_path.unlink()
                    deleted_count += 1
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old files in {directory}: {e}")
        return 0

def get_directory_size(directory: str) -> int:
    """
    Get total size of directory in bytes.
    """
    try:
        total_size = 0
        for file_path in Path(directory).rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
        
    except Exception as e:
        logger.error(f"Failed to get directory size for {directory}: {e}")
        return 0
