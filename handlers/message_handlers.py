"""
Message handlers for processing user text messages
"""

import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from services.openai_service import OpenAIService
from services.gemini_service import GeminiService
from services.together_service import TogetherService

logger = logging.getLogger(__name__)

class MessageHandlers:
    """Handles user text messages and AI responses"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = bot_instance.config
        self.rate_limiter = bot_instance.rate_limiter
        self.conversation_manager = bot_instance.conversation_manager
        
        # Initialize AI services
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available AI services"""
        if self.config.openai_api_key:
            try:
                self.services['openai'] = OpenAIService(self.config.openai_api_key)
                logger.info("OpenAI service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI service: {e}")
        
        if self.config.gemini_api_key:
            try:
                self.services['gemini'] = GeminiService(self.config.gemini_api_key)
                logger.info("Gemini service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini service: {e}")
        
        if self.config.together_api_key:
            try:
                self.services['together'] = TogetherService(self.config.together_api_key)
                logger.info("Together AI service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Together AI service: {e}")
        
        if not self.services:
            logger.error("No AI services were successfully initialized!")
    
    def _get_service_for_model(self, model: str):
        """Get the appropriate service for a given model"""
        model_lower = model.lower()
        
        if 'gpt' in model_lower or 'openai' in model_lower:
            return self.services.get('openai')
        elif 'gemini' in model_lower:
            return self.services.get('gemini')  
        elif 'llama' in model_lower or 'mistral' in model_lower:
            return self.services.get('together')
        
        return None
    
    def _auto_select_service(self):
        """Automatically select best available service"""
        # Prefer OpenAI GPT-4o-mini for general use (fast and cost-effective)
        if 'openai' in self.services:
            return self.services['openai'], "gpt-4o-mini"
        
        # Fall back to Gemini Flash (fast)
        if 'gemini' in self.services:
            return self.services['gemini'], "gemini-2.5-flash"
        
        # Finally Together AI with Llama
        if 'together' in self.services:
            return self.services['together'], "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        
        return None, None
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        
        # Check rate limiting (skip for admins)
        if not self.config.is_admin(user_id):
            is_allowed, rate_info = self.rate_limiter.is_allowed(user_id)
            
            if not is_allowed:
                retry_after = rate_info['retry_after']
                await update.message.reply_text(
                    f"⏱️ **Rate Limit Exceeded**\n\n"
                    f"You've reached the limit of {self.config.rate_limit_messages} messages per hour.\n"
                    f"Please try again in {retry_after // 60} minutes and {retry_after % 60} seconds.\n\n"
                    f"Remaining requests: {rate_info['remaining']}"
                )
                return
        
        # Show typing indicator
        await update.message.chat.send_action(action="typing")
        
        try:
            # Determine which model/service to use
            selected_model = context.user_data.get('selected_model', 'auto')
            
            if selected_model == 'auto':
                service, model = self._auto_select_service()
                if not service:
                    await update.message.reply_text(
                        "❌ No AI services are currently available. Please contact an administrator."
                    )
                    return
            else:
                # User selected specific model
                service = self._get_service_for_model(selected_model)
                model = selected_model
                
                if not service:
                    await update.message.reply_text(
                        f"❌ The selected model `{selected_model}` is not available.\n"
                        f"Available services: {', '.join(self.services.keys())}\n\n"
                        f"Use `/model` to select a different model or choose auto-select."
                    )
                    return
            
            # Get conversation history
            conversation = self.conversation_manager.get_conversation(user_id)
            
            # Add user message to conversation
            self.conversation_manager.add_message(user_id, "user", message_text)
            
            # Prepare messages for AI service
            messages = []
            
            # Add system message
            system_message = (
                f"You are AstroGeminiBot, a helpful AI assistant. "
                f"You're currently using the {model} model. "
                f"Be conversational, helpful, and concise. "
                f"The user's name is {user.first_name}."
            )
            messages.append({"role": "system", "content": system_message})
            
            # Add conversation history
            for msg in conversation:
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": message_text})
            
            # Generate AI response
            logger.info(f"Generating response for user {user_id} using {service.provider_name} - {model}")
            
            start_time = asyncio.get_event_loop().time()
            response_data = await service.generate_response(
                messages=messages,
                model=model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature
            )
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            ai_response = response_data['content']
            usage = response_data.get('usage', {})
            
            # Add AI response to conversation
            self.conversation_manager.add_message(user_id, "assistant", ai_response)
            
            # Format response with metadata (for debugging/info)
            footer = f"\n\n`{response_data['provider']} • {model} • {response_time:.1f}s"
            if usage.get('total_tokens'):
                footer += f" • {usage['total_tokens']} tokens`"
            else:
                footer += "`"
            
            # Send response (split if too long)
            full_response = ai_response + footer
            
            if len(full_response) > 4096:
                # Split long messages
                await update.message.reply_text(ai_response)
                await update.message.reply_text(footer, parse_mode='Markdown')
            else:
                await update.message.reply_text(full_response, parse_mode='Markdown')
            
            logger.info(
                f"Response sent to user {user_id}: {len(ai_response)} chars, "
                f"{usage.get('total_tokens', 'unknown')} tokens, {response_time:.1f}s"
            )
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}", exc_info=True)
            
            # Try to get a user-friendly error message
            if hasattr(service, 'format_error'):
                error_message = service.format_error(e)
            else:
                error_message = f"❌ Sorry, I encountered an error: {str(e)[:100]}..."
            
            await update.message.reply_text(error_message)
            
            # If this was the selected service failing, suggest auto-select
            if selected_model != 'auto':
                await update.message.reply_text(
                    "💡 **Tip**: Try using `/model` and selecting 'Auto Select' for better reliability."
                )
