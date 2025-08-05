import os
from dotenv import load_dotenv
from typing import Dict
import logging

class Config:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Load environment variables
        load_dotenv()
        
        # Log environment variables status
        self.logger.info("Checking environment variables...")
        
        # API Configuration
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        # Log API key status
        self.logger.info(f"OpenRouter API Key present: {bool(self.openrouter_api_key)}")
        
        # Platform Settings
        self.supported_platforms = {
            "instagram": {
                "max_hashtags": int(os.getenv('MAX_HASHTAGS', '30')),
                "character_limit": 2200,
                "image_formats": ["jpg", "png"],
                "aspect_ratios": ["1:1", "4:5", "16:9"]
            },
            "twitter": {
                "max_hashtags": 2,
                "character_limit": 280,
                "image_formats": ["jpg", "png", "gif"],
                "aspect_ratios": ["16:9"]
            },
            "linkedin": {
                "max_hashtags": 3,
                "character_limit": 3000,
                "image_formats": ["jpg", "png"],
                "aspect_ratios": ["1.91:1"]
            },
            "facebook": {
                "max_hashtags": 2,
                "character_limit": 63206,
                "image_formats": ["jpg", "png", "gif"],
                "aspect_ratios": ["1.91:1", "16:9"]
            },
            "tiktok": {
                "max_hashtags": 5,
                "character_limit": 2200,
                "image_formats": ["jpg", "png"],
                "aspect_ratios": ["9:16"]
            }
        }
        
        # Agent Settings with OpenRouter Models
        self.agent_settings = {
            "content_strategist": {
                "temperature": float(os.getenv('CONTENT_STRATEGIST_TEMPERATURE', '0.7')),
                "model": os.getenv('CONTENT_STRATEGIST_MODEL', 'openai/gpt-3.5-turbo')
            },
            "content_writer": {
                "temperature": float(os.getenv('CONTENT_WRITER_TEMPERATURE', '0.8')),
                "model": os.getenv('CONTENT_WRITER_MODEL', 'openai/gpt-3.5-turbo')
            },
            "hashtag_specialist": {
                "temperature": float(os.getenv('HASHTAG_SPECIALIST_TEMPERATURE', '0.6')),
                "model": os.getenv('HASHTAG_SPECIALIST_MODEL', 'openai/gpt-3.5-turbo')
            },
            "visual_designer": {
                "temperature": float(os.getenv('VISUAL_DESIGNER_TEMPERATURE', '0.7')),
                "model": os.getenv('VISUAL_DESIGNER_MODEL', 'openai/gpt-3.5-turbo')
            }
        }

    def get_platform_settings(self, platform: str) -> Dict:
        """
        Get settings for a specific platform.
        
        Args:
            platform (str): The social media platform
            
        Returns:
            Dict: Platform-specific settings
        """
        return self.supported_platforms.get(platform.lower(), {})
        
    def get_agent_settings(self, agent_name: str) -> Dict:
        """
        Get settings for a specific agent.
        
        Args:
            agent_name (str): The name of the agent
            
        Returns:
            Dict: Agent-specific settings
        """
        return self.agent_settings.get(agent_name, {})
        
    def validate_api_keys(self) -> bool:
        """
        Validate that all required API keys are present.
        
        Returns:
            bool: True if all required keys are present
        """
        if not self.openrouter_api_key:
            self.logger.error("OpenRouter API key is missing!")
            return False
            
        return True

    @property
    def available_platforms(self) -> list:
        """
        Get list of supported platforms.
        
        Returns:
            list: List of supported platform names
        """
        return list(self.supported_platforms.keys()) 