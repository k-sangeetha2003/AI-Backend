import re
from typing import List, Set
import logging

from app.models.schemas import SafetyResult

logger = logging.getLogger(__name__)

class SafetyService:
    def __init__(self):
        # NSFW keywords
        self.nsfw_keywords = {
            'nsfw', 'nude', 'naked', 'explicit', 'adult', 'porn', 'xxx',
            'sexual', 'inappropriate', 'offensive', 'erotic', 'lewd'
        }
        
        # Hate speech keywords
        self.hate_speech_keywords = {
            'hate', 'racist', 'discrimination', 'bigotry', 'prejudice'
        }
        
        # Political keywords
        self.political_keywords = {
            'politics', 'political', 'election', 'vote', 'campaign'
        }
    
    def check_prompt_safety(self, prompt: str) -> SafetyResult:
        """
        Check if prompt contains inappropriate content.
        """
        try:
            prompt_lower = prompt.lower()
            
            # Check for NSFW content
            for keyword in self.nsfw_keywords:
                if keyword in prompt_lower:
                    return SafetyResult(
                        is_safe=False,
                        reason=f"Contains inappropriate keyword: {keyword}",
                        category="nsfw",
                        confidence=0.9
                    )
            
            # Check for hate speech
            for keyword in self.hate_speech_keywords:
                if keyword in prompt_lower:
                    return SafetyResult(
                        is_safe=False,
                        reason=f"Contains hate speech keyword: {keyword}",
                        category="hate_speech",
                        confidence=0.8
                    )
            
            # Check for political content
            for keyword in self.political_keywords:
                if keyword in prompt_lower:
                    return SafetyResult(
                        is_safe=False,
                        reason=f"Contains political keyword: {keyword}",
                        category="political",
                        confidence=0.7
                    )
            
            # Check for excessive repetition
            if self._has_excessive_repetition(prompt):
                return SafetyResult(
                    is_safe=False,
                    reason="Excessive repetition detected",
                    category="spam",
                    confidence=0.6
                )
            
            return SafetyResult(
                is_safe=True,
                reason="Prompt passed safety checks",
                category="safe",
                confidence=1.0
            )
            
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return SafetyResult(
                is_safe=False,
                reason="Safety check error",
                category="error",
                confidence=0.0
            )
    
    def _has_excessive_repetition(self, prompt: str) -> bool:
        """
        Check for excessive repetition in prompt.
        """
        words = prompt.lower().split()
        if len(words) < 3:
            return False
        
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Check if any word appears more than 50% of the time
        max_count = max(word_counts.values())
        return max_count > len(words) * 0.5

    def is_safe(self, prompt: str) -> (bool, str):
        prompt_lower = prompt.lower()
        for keyword in self.nsfw_keywords:
            if keyword in prompt_lower:
                return False, f"Unsafe content detected: '{keyword}'"
        return True, ""
