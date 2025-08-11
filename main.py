#!/usr/bin/env python3
"""
AstroGeminiBot - Multi-AI Provider Telegram Bot
Main entry point for the application
"""

import asyncio
import logging
import os
from bot import AstroGeminiBot
from utils.logger import setup_logging

def main():
    """Main function to start the bot"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check required environment variables
    required_env_vars = ['TELEGRAM_BOT_TOKEN']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration")
        return
    
    # Check if at least one AI provider is configured
    ai_providers = ['GEMINI_API_KEY', 'TOGETHER_API_KEY']
    available_providers = [var for var in ai_providers if os.getenv(var)]
    
    if not available_providers:
        logger.error("No AI providers configured. Please set at least one of: OPENAI_API_KEY, GEMINI_API_KEY, TOGETHER_API_KEY")
        return
    
    logger.info(f"Available AI providers: {', '.join([var.split('_')[0] for var in available_providers])}")
    
    try:
        # Create and run bot
        bot = AstroGeminiBot()
        bot.start_info()
        
        # Use Application.run_polling() directly instead of asyncio.run()
        bot.application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed with error: {e}", exc_info=True)

if __name__ == '__main__':
    main()
