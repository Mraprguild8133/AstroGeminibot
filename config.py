"""
Configuration management for AstroGeminiBot
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for bot settings"""
    
    def __init__(self):
        # Telegram Bot Token (Required)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        # AI Provider API Keys
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.together_api_key = os.getenv("TOGETHER_API_KEY")
        
        # Rate Limiting Settings
        self.rate_limit_messages = int(os.getenv("RATE_LIMIT_MESSAGES", "20"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  # 1 hour in seconds
        
        # AI Model Settings
        self.default_model = os.getenv("DEFAULT_MODEL", "auto")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1500"))
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Conversation Settings
        self.max_conversation_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "10"))
        self.conversation_timeout = int(os.getenv("CONVERSATION_TIMEOUT", "3600"))  # 1 hour
        
        # Logging Settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "bot.log")
        
        # Admin Settings
        admin_ids = os.getenv("ADMIN_USER_IDS", "")
        self.admin_user_ids = [int(uid.strip()) for uid in admin_ids.split(",") if uid.strip()]
    
    def get_available_services(self) -> List[str]:
        """Get list of available AI services based on API keys"""
        services = []
        if self.openai_api_key:
            services.append("OpenAI")
        if self.gemini_api_key:
            services.append("Gemini")
        if self.together_api_key:
            services.append("Together")
        return services
    
    def get_model_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available models"""
        models = {}
        
        if self.openai_api_key:
            models.update({
                "gpt-4o": {
                    "provider": "OpenAI",
                    "description": "Most capable GPT model",
                    "emoji": "🚀"
                },
                "gpt-4o-mini": {
                    "provider": "OpenAI", 
                    "description": "Fast and cost-effective",
                    "emoji": "⚡"
                }
            })
        
        if self.gemini_api_key:
            models.update({
                "gemini-2.5-flash": {
                    "provider": "Gemini",
                    "description": "Fast Gemini model",
                    "emoji": "💎"
                },
                "gemini-2.5-pro": {
                    "provider": "Gemini",
                    "description": "Most capable Gemini model", 
                    "emoji": "💠"
                }
            })
        
        if self.together_api_key:
            models.update({
                "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": {
                    "provider": "Together",
                    "description": "Llama 3.1 70B",
                    "emoji": "🦙"
                },
                "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo": {
                    "provider": "Together", 
                    "description": "Llama 3.1 8B (Fast)",
                    "emoji": "🐎"
                }
            })
        


        return models
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in self.admin_user_ids
