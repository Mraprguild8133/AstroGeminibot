"""
Base AI service class that defines the interface for all AI providers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseAIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.provider_name = self.__class__.__name__.replace('Service', '')
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]], 
        model: str = None,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate AI response from conversation messages
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Specific model to use (optional)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)
        
        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this service"""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this service"""
        pass
    
    def format_error(self, error: Exception) -> str:
        """Format error message for user display"""
        error_msg = str(error).lower()
        
        if 'api key' in error_msg or 'unauthorized' in error_msg:
            return f"❌ {self.provider_name} API key is invalid or missing"
        elif 'quota' in error_msg or 'billing' in error_msg:
            return f"❌ {self.provider_name} quota exceeded or billing issue"
        elif 'rate limit' in error_msg:
            return f"❌ {self.provider_name} rate limit exceeded. Please try again later"
        elif 'timeout' in error_msg:
            return f"❌ {self.provider_name} request timed out. Please try again"
        elif 'network' in error_msg or 'connection' in error_msg:
            return f"❌ Network error connecting to {self.provider_name}"
        else:
            return f"❌ {self.provider_name} error: {str(error)[:100]}..."
    
    async def health_check(self) -> bool:
        """Check if the service is available and API key is valid"""
        try:
            # Simple test with minimal usage
            test_messages = [{"role": "user", "content": "Hi"}]
            await self.generate_response(test_messages, max_tokens=10)
            return True
        except Exception as e:
            logger.warning(f"{self.provider_name} health check failed: {e}")
            return False
