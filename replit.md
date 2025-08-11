# AstroGeminiBot

## Overview

AstroGeminiBot is a multi-AI provider Telegram bot that allows users to interact with various AI models through a unified chat interface. The bot supports OpenAI, Google Gemini, and Together AI services, providing users with flexibility to choose between different AI providers and models. Key features include conversation context management, rate limiting, usage statistics, and administrative controls.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

**August 11, 2025:**
- Successfully deployed AstroGeminiBot with multi-AI provider support
- Confirmed working integration with OpenAI, Gemini, and Together AI services
- AIMLAPI integration was temporarily added then completely removed per user request
- Tested failover system - automatically switches providers when quota limits are reached
- Bot is live and responding to user messages via Telegram
- Verified rate limiting, conversation management, and command handlers are working

## System Architecture

### Core Architecture Pattern
The application follows a modular, handler-based architecture with clear separation of concerns:

**Main Components:**
- **Bot Core (`bot.py`)**: Central orchestrator that initializes all components and manages the Telegram application lifecycle
- **Configuration Management (`config.py`)**: Centralized environment-based configuration with validation
- **Handler System**: Separate modules for command processing and message handling
- **Service Layer**: Abstract AI service interface with provider-specific implementations
- **Utility Components**: Conversation management, rate limiting, and logging utilities

### AI Service Architecture
The bot implements a plugin-like architecture for AI providers using the Strategy pattern:

**Base Service Interface (`BaseAIService`)**: Defines a common contract for all AI providers with methods for response generation, model listing, and error handling.

**Provider Implementations**: 
- OpenAI Service (GPT models)
- Gemini Service (Google AI models) 
- Together AI Service (Open source models like Llama, Mixtral)

**Model Selection**: Supports automatic model selection and user-specified models, with each service maintaining its own list of available models.

### Conversation Management
**In-Memory Context Storage**: Conversations are stored in memory with automatic cleanup based on configurable timeouts and message limits. Each user's conversation includes message history, timestamps, and activity tracking.

**Message Flow**: User messages are processed through rate limiting, then routed to the selected AI service, with responses stored in conversation context for future interactions.

### Rate Limiting System
**Sliding Window Implementation**: Uses an in-memory deque-based system to track user requests within configurable time windows. Includes comprehensive statistics tracking for monitoring usage patterns and blocked requests.

### Error Handling Strategy
**Graceful Degradation**: The system handles missing API keys by simply not initializing those services, allowing the bot to function with any available AI provider. Comprehensive error logging and user-friendly error messages are provided throughout.

## External Dependencies

### AI Service Providers
- **OpenAI API**: Primary AI service for GPT models (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
- **Google Gemini API**: Google's AI models (gemini-2.5-flash, gemini-2.5-pro, gemini-1.5-pro, gemini-1.5-flash)
- **Together AI API**: Access to open-source models (Meta-Llama, Mixtral, Mistral variants)

### Telegram Integration
- **python-telegram-bot**: Official Python library for Telegram Bot API integration, handles all bot communication, command processing, and callback management

### HTTP Client Library
- **httpx**: Async HTTP client used specifically for Together AI API calls, providing reliable HTTP communication with proper timeout handling

### Environment Management
- **python-dotenv**: Loads configuration from .env files, enabling secure credential management and environment-specific settings

### Authentication Requirements
All AI services require API keys for authentication:
- `TELEGRAM_BOT_TOKEN` (required)
- `OPENAI_API_KEY` (optional)
- `GEMINI_API_KEY` (optional) 
- `TOGETHER_API_KEY` (optional)

At least one AI provider API key must be configured for the bot to function.