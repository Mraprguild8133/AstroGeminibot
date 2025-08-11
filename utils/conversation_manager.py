"""
Conversation context management for maintaining chat history
"""

import time
import logging
from typing import Dict, List, Any
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation context and history for users"""
    
    def __init__(self, max_history: int = 10, timeout_seconds: int = 3600):
        self.max_history = max_history
        self.timeout_seconds = timeout_seconds
        
        # Store conversations: user_id -> {'messages': [...], 'created_at': timestamp, 'last_activity': timestamp}
        self.conversations: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            'messages': [],
            'created_at': time.time(),
            'last_activity': time.time()
        })
    
    def add_message(self, user_id: int, role: str, content: str):
        """Add a message to user's conversation history"""
        
        conversation = self.conversations[user_id]
        current_time = time.time()
        
        # Check if conversation has timed out
        if current_time - conversation['last_activity'] > self.timeout_seconds:
            logger.info(f"Conversation timeout for user {user_id}, clearing history")
            conversation['messages'] = []
            conversation['created_at'] = current_time
        
        # Add the new message
        conversation['messages'].append({
            'role': role,
            'content': content,
            'timestamp': current_time
        })
        
        # Update last activity
        conversation['last_activity'] = current_time
        
        # Trim conversation if it exceeds max history
        if len(conversation['messages']) > self.max_history:
            # Keep system messages and trim user/assistant pairs
            messages = conversation['messages']
            system_messages = [msg for msg in messages if msg['role'] == 'system']
            other_messages = [msg for msg in messages if msg['role'] != 'system']
            
            # Keep the most recent messages
            if len(other_messages) > self.max_history - len(system_messages):
                other_messages = other_messages[-(self.max_history - len(system_messages)):]
            
            conversation['messages'] = system_messages + other_messages
        
        logger.debug(f"Added {role} message for user {user_id}, conversation length: {len(conversation['messages'])}")
    
    def get_conversation(self, user_id: int) -> List[Dict[str, str]]:
        """Get conversation history for a user (without timestamps)"""
        
        conversation = self.conversations[user_id]
        current_time = time.time()
        
        # Check if conversation has timed out
        if current_time - conversation['last_activity'] > self.timeout_seconds:
            logger.info(f"Conversation timeout for user {user_id}, returning empty history")
            return []
        
        # Return messages without timestamps for AI service
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in conversation['messages']
        ]
    
    def clear_conversation(self, user_id: int):
        """Clear conversation history for a user"""
        
        if user_id in self.conversations:
            current_time = time.time()
            self.conversations[user_id] = {
                'messages': [],
                'created_at': current_time,
                'last_activity': current_time
            }
            logger.info(f"Cleared conversation for user {user_id}")
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        
        conversation = self.conversations[user_id]
        
        created_at = datetime.fromtimestamp(conversation['created_at']).strftime('%Y-%m-%d %H:%M')
        last_activity = datetime.fromtimestamp(conversation['last_activity']).strftime('%Y-%m-%d %H:%M')
        
        # Count messages by role
        messages = conversation['messages']
        role_counts = {}
        for msg in messages:
            role = msg['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Check if conversation is active (not timed out)
        current_time = time.time()
        is_active = (current_time - conversation['last_activity']) <= self.timeout_seconds
        
        return {
            'message_count': len(messages),
            'role_counts': role_counts,
            'created_at': created_at,
            'last_activity': last_activity,
            'is_active': is_active,
            'timeout_in': max(0, int(self.timeout_seconds - (current_time - conversation['last_activity'])))
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global conversation statistics"""
        
        total_users = len(self.conversations)
        total_messages = sum(len(conv['messages']) for conv in self.conversations.values())
        
        current_time = time.time()
        active_users = sum(
            1 for conv in self.conversations.values()
            if (current_time - conv['last_activity']) <= self.timeout_seconds
        )
        
        # Average messages per user
        avg_messages = total_messages / total_users if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_messages': total_messages,
            'average_messages_per_user': avg_messages,
            'timeout_seconds': self.timeout_seconds,
            'max_history_per_user': self.max_history
        }
    
    def cleanup_expired_conversations(self):
        """Remove expired conversations to free memory"""
        
        current_time = time.time()
        expired_users = []
        
        for user_id, conversation in self.conversations.items():
            if (current_time - conversation['last_activity']) > (self.timeout_seconds * 2):  # Double timeout for cleanup
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.conversations[user_id]
            logger.info(f"Cleaned up expired conversation for user {user_id}")
        
        if expired_users:
            logger.info(f"Cleaned up {len(expired_users)} expired conversations")
        
        return len(expired_users)
