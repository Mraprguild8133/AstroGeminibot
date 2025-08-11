"""
Google Gemini service implementation
"""

import asyncio
import logging
from typing import List, Dict, Any
from google import genai
from google.genai import types
from .base_ai_service import BaseAIService

logger = logging.getLogger(__name__)

class GeminiService(BaseAIService):
    """Google Gemini API service implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.client = genai.Client(api_key=api_key)
        
        # Available models - newest Gemini model series is "gemini-2.5-flash" or "gemini-2.5-pro"
        # do not change this unless explicitly requested by the user
        self.models = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate response using Gemini API"""
        
        if model is None:
            model = self.get_default_model()
        
        try:
            # Convert messages to Gemini format
            contents = []
            system_instruction = None
            
            for message in messages:
                role = message['role']
                content = message['content']
                
                if role == 'system':
                    system_instruction = content
                elif role == 'user':
                    contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
                elif role == 'assistant':
                    contents.append(types.Content(role="model", parts=[types.Part(text=content)]))
            
            # If no system instruction from messages, use default
            if not system_instruction:
                system_instruction = "You are a helpful AI assistant."
            
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            # Run in thread pool since Gemini client might be blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
            )
            
            content = response.text or "No response generated"
            
            # Gemini doesn't provide detailed usage stats in the same way
            usage = {
                'prompt_tokens': len(' '.join(msg['content'] for msg in messages)) // 4,  # Rough estimate
                'completion_tokens': len(content) // 4,  # Rough estimate
                'total_tokens': 0
            }
            usage['total_tokens'] = usage['prompt_tokens'] + usage['completion_tokens']
            
            return {
                'content': content,
                'model': model,
                'provider': 'Gemini',
                'usage': usage
            }
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise e
    
    def get_available_models(self) -> List[str]:
        """Get available Gemini models"""
        return self.models.copy()
    
    def get_default_model(self) -> str:
        """Get default Gemini model"""
        return "gemini-2.5-flash"  # Fast and efficient default
