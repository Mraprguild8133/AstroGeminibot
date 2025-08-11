"""
Main bot class for AstroGeminiBot
Handles Telegram bot initialization and routing
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters, 
    ContextTypes
)

from config import Config
from rate_limiter import RateLimiter
from utils.conversation_manager import ConversationManager
from handlers.command_handlers import CommandHandlers
from handlers.message_handlers import MessageHandlers

logger = logging.getLogger(__name__)

class AstroGeminiBot:
    """Main bot class that orchestrates all components"""
    
    def __init__(self):
        self.config = Config()
        self.rate_limiter = RateLimiter()
        self.conversation_manager = ConversationManager()
        self.command_handlers = CommandHandlers(self)
        self.message_handlers = MessageHandlers(self)
        
        # Initialize Telegram application
        self.application = Application.builder().token(
            self.config.telegram_bot_token
        ).build()
        
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all bot handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.command_handlers.start))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help))
        self.application.add_handler(CommandHandler("model", self.command_handlers.model))
        self.application.add_handler(CommandHandler("stats", self.command_handlers.stats))
        self.application.add_handler(CommandHandler("clear", self.command_handlers.clear))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.command_handlers.button_callback))
        
        # Message handlers
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handlers.handle_text)
        )
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors that occur during bot operation"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
        
        if update and update.effective_chat:
            try:
                await update.effective_chat.send_message(
                    "❌ An unexpected error occurred. Please try again later."
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")
    
    def start_info(self):
        """Log startup information"""
        logger.info("Starting AstroGeminiBot...")
        logger.info(f"Available AI services: {', '.join(self.config.get_available_services())}")
