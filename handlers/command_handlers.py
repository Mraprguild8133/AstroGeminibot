"""
Command handlers for the Telegram bot
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class CommandHandlers:
    """Handles all bot commands"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.config = bot_instance.config
        self.rate_limiter = bot_instance.rate_limiter
        self.conversation_manager = bot_instance.conversation_manager
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        welcome_message = f"""
🤖 **Welcome to AstroGeminiBot, {user.first_name}!**

I'm an AI-powered bot that can chat with you using multiple AI providers:
{', '.join(self.config.get_available_services())}

**Available Commands:**
• `/help` - Show detailed help
• `/model` - Choose AI model  
• `/stats` - View your usage stats
• `/clear` - Clear conversation history

**Features:**
✨ Multiple AI models support
🛡️ Rate limiting protection  
💬 Conversation context memory
📊 Usage statistics

Just send me any message to start chatting!
        """
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        
        available_models = self.config.get_model_info()
        model_list = "\n".join([
            f"• `{model}` {info['emoji']} - {info['description']}"
            for model, info in available_models.items()
        ])
        
        help_message = f"""
🔍 **AstroGeminiBot Help**

**Available AI Models:**
{model_list}

**Commands:**
• `/start` - Welcome message
• `/help` - This help message
• `/model` - Select AI model to use
• `/stats` - View usage statistics  
• `/clear` - Clear conversation history

**Features:**
🔄 **Auto Model Selection**: I'll choose the best available model
💬 **Context Aware**: I remember our conversation
⚡ **Rate Limited**: {self.config.rate_limit_messages} messages per hour
🔒 **Privacy**: Conversations are stored temporarily

**Usage:**
Simply send me any message and I'll respond using AI. You can ask questions, have conversations, or request help with various topics.

**Rate Limits:**
• {self.config.rate_limit_messages} messages per {self.config.rate_limit_window // 60} minutes
• Admins have unlimited access

Need more help? Just ask me anything!
        """
        
        await update.message.reply_text(
            help_message,
            parse_mode='Markdown'
        )
    
    async def model(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /model command - show model selection"""
        
        available_models = self.config.get_model_info()
        
        if not available_models:
            await update.message.reply_text("❌ No AI models are currently available.")
            return
        
        # Create inline keyboard with model options
        keyboard = []
        for model, info in available_models.items():
            button_text = f"{info['emoji']} {model} ({info['provider']})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"model_{model}")])
        
        # Add auto-select option
        keyboard.append([InlineKeyboardButton("🤖 Auto Select (Recommended)", callback_data="model_auto")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        current_model = context.user_data.get('selected_model', 'auto')
        
        await update.message.reply_text(
            f"🔧 **Model Selection**\n\n"
            f"Current: `{current_model}`\n\n"
            f"Choose an AI model to use for our conversations:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command - show user statistics"""
        
        user_id = update.effective_user.id
        user_stats = self.rate_limiter.get_user_stats(user_id)
        conv_stats = self.conversation_manager.get_user_stats(user_id)
        
        is_admin = self.config.is_admin(user_id)
        
        # Format timestamps
        first_request = "Never"
        last_request = "Never"
        
        if user_stats['first_request']:
            first_request = datetime.fromtimestamp(user_stats['first_request']).strftime('%Y-%m-%d %H:%M')
        
        if user_stats['last_request']:
            last_request = datetime.fromtimestamp(user_stats['last_request']).strftime('%Y-%m-%d %H:%M')
        
        # Calculate success rate
        total_requests = user_stats['total_requests']
        blocked_requests = user_stats['blocked_requests']
        success_rate = ((total_requests - blocked_requests) / total_requests * 100) if total_requests > 0 else 100
        
        stats_message = f"""
📊 **Your Usage Statistics**

**Rate Limiting:**
• Remaining requests: {user_stats['remaining_requests']}/{self.config.rate_limit_messages}
• Total requests: {total_requests}
• Blocked requests: {blocked_requests}
• Success rate: {success_rate:.1f}%

**Conversation:**
• Messages in history: {conv_stats['message_count']}
• Active since: {conv_stats['created_at']}
• Last activity: {conv_stats['last_activity']}

**Account:**
• User ID: `{user_id}`
• Admin status: {"✅ Yes" if is_admin else "❌ No"}
• First request: {first_request}
• Last request: {last_request}

**Current Settings:**
• Selected model: `{context.user_data.get('selected_model', 'auto')}`
• Max conversation history: {self.config.max_conversation_history} messages
        """
        
        # Add admin stats if user is admin
        if is_admin:
            global_stats = self.rate_limiter.get_global_stats()
            stats_message += f"""

**Global Stats (Admin):**
• Total users: {global_stats['total_users']}
• Active users: {global_stats['active_users']}
• Global requests: {global_stats['total_requests']}
• Global success rate: {global_stats['success_rate']:.1f}%
            """
        
        await update.message.reply_text(
            stats_message,
            parse_mode='Markdown'
        )
    
    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /clear command - clear conversation history"""
        
        user_id = update.effective_user.id
        self.conversation_manager.clear_conversation(user_id)
        
        await update.message.reply_text(
            "🗑️ **Conversation Cleared**\n\n"
            "Your conversation history has been cleared. We can start fresh!"
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data.startswith("model_"):
            model = callback_data[6:]  # Remove "model_" prefix
            
            if model == "auto":
                context.user_data['selected_model'] = "auto"
                response_text = "🤖 **Auto Model Selection Enabled**\n\nI'll automatically choose the best available model for each conversation."
            else:
                context.user_data['selected_model'] = model
                model_info = self.config.get_model_info().get(model, {})
                provider = model_info.get('provider', 'Unknown')
                description = model_info.get('description', 'AI Model')
                emoji = model_info.get('emoji', '🤖')
                
                response_text = f"{emoji} **Model Selected: {model}**\n\n" \
                               f"Provider: {provider}\n" \
                               f"Description: {description}\n\n" \
                               f"All future conversations will use this model until you change it."
            
            await query.edit_message_text(
                response_text,
                parse_mode='Markdown'
            )
