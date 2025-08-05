#!/usr/bin/env python3
"""
Logging utility for Short Story Crew
Creates daily log files and provides structured logging across the application.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class StoryCrewLogger:
    """Custom logger for the Short Story Crew application."""

    def __init__(self, name: str = "short_story_crew", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper())
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """Set up the logger with both file and console handlers."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)

        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)8s | %(module)s.%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)8s | %(message)s", datefmt="%H:%M:%S"
        )

        # File handler with daily rotation
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_dir / f"story_crew_{today}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)

        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"Logger initialized - Log file: {log_file}")

    def get_logger(self):
        """Get the configured logger instance."""
        return self.logger


# Global logger instance
_logger_instance = None


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up and return the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StoryCrewLogger(log_level=log_level)
    return _logger_instance.get_logger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for a specific module."""
    if _logger_instance is None:
        setup_logging()

    if name:
        # Create a child logger for specific modules
        child_logger = _logger_instance.get_logger().getChild(name)
        return child_logger
    else:
        return _logger_instance.get_logger()


# Convenience functions for different log levels
def log_info(message: str, module: str = None):
    """Log an info message."""
    logger = get_logger(module)
    logger.info(message)


def log_warning(message: str, module: str = None):
    """Log a warning message."""
    logger = get_logger(module)
    logger.warning(message)


def log_error(message: str, module: str = None, exc_info: bool = False):
    """Log an error message."""
    logger = get_logger(module)
    logger.error(message, exc_info=exc_info)


def log_debug(message: str, module: str = None):
    """Log a debug message."""
    logger = get_logger(module)
    logger.debug(message)


def log_crew_action(crew_member: str, action: str, details: str = ""):
    """Log crew member actions with specific formatting."""
    message = f"🎭 {crew_member}: {action}"
    if details:
        message += f" | {details}"
    log_info(message, "crew_action")


def log_task_progress(task_name: str, status: str, details: str = ""):
    """Log task progress with specific formatting."""
    status_emoji = {
        "started": "🚀",
        "completed": "✅",
        "failed": "❌",
        "in_progress": "⏳",
    }

    emoji = status_emoji.get(status.lower(), "📋")
    message = f"{emoji} Task [{task_name}]: {status.upper()}"
    if details:
        message += f" | {details}"

    if status.lower() == "failed":
        log_error(message, "task_progress")
    else:
        log_info(message, "task_progress")


def log_user_interaction(action: str, details: str = ""):
    """Log user interactions."""
    message = f"👤 User: {action}"
    if details:
        message += f" | {details}"
    log_info(message, "user_interaction")


def log_story_generation(stage: str, genre: str, idea: str, details: str = ""):
    """Log story generation progress."""
    message = f"📖 Story Generation [{stage}] | Genre: {genre} | Idea: {idea[:50]}..."
    if details:
        message += f" | {details}"
    log_info(message, "story_generation")
