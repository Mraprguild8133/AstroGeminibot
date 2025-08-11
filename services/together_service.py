"""
Together AI service implementation
"""

import asyncio
import logging
import httpx
from typing import List, Dict, Any
from .base_ai_service import BaseAIService

logger = logging.getLogger(__name__)

class TogetherService(BaseAIService):
    """Together AI API service implementation"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.api_key = api_key
        self.base_url = "https://api.together.xyz/v1"
        
        # Available models on Together AI
        self.models = [
            "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
            "meta-llama/Meta-Llama-3-8B-Instruct-Turbo",
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "mistralai/Mistral-7B-Instruct-v0.1"
        ]
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Generate response using Together AI API"""
        
        if model is None:
            model = self.get_default_model()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "stop": ["<|eot_id|>", "<|end_of_text|>"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                data = response.json()
                
                if 'choices' not in data or not data['choices']:
                    raise Exception("No response choices returned")
                
                content = data['choices'][0]['message']['content']
                usage = data.get('usage', {})
                
                return {
                    'content': content,
                    'model': model,
                    'provider': 'Together',
                    'usage': {
                        'prompt_tokens': usage.get('prompt_tokens', 0),
                        'completion_tokens': usage.get('completion_tokens', 0),
                        'total_tokens': usage.get('total_tokens', 0)
                    }
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception("Invalid Together AI API key")
            elif e.response.status_code == 429:
                raise Exception("Together AI rate limit exceeded")
            else:
                raise Exception(f"Together AI HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Together AI API error: {e}")
            raise e
    
    def get_available_models(self) -> List[str]:
        """Get available Together AI models"""
        return self.models.copy()
    
    def get_default_model(self) -> str:
        """Get default Together AI model"""
        return "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"  # Fast and capable default
