"""
Rate limiting functionality for the bot
"""

import time
import logging
from typing import Dict, List, Tuple
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self, max_requests: int = 20, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests: Dict[int, deque] = defaultdict(deque)
        self.user_stats: Dict[int, Dict] = defaultdict(lambda: {
            'total_requests': 0,
            'blocked_requests': 0,
            'first_request': None,
            'last_request': None
        })
    
    def is_allowed(self, user_id: int) -> Tuple[bool, Dict]:
        """
        Check if user is allowed to make a request
        Returns (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        user_queue = self.user_requests[user_id]
        
        # Remove expired requests from the queue
        while user_queue and user_queue[0] <= current_time - self.window_seconds:
            user_queue.popleft()
        
        # Update stats
        stats = self.user_stats[user_id]
        stats['total_requests'] += 1
        stats['last_request'] = current_time
        if stats['first_request'] is None:
            stats['first_request'] = current_time
        
        # Check if user has exceeded rate limit
        if len(user_queue) >= self.max_requests:
            stats['blocked_requests'] += 1
            oldest_request = user_queue[0]
            reset_time = oldest_request + self.window_seconds
            
            rate_limit_info = {
                'remaining': 0,
                'reset_at': reset_time,
                'retry_after': int(reset_time - current_time)
            }
            
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False, rate_limit_info
        
        # Add current request to queue
        user_queue.append(current_time)
        
        rate_limit_info = {
            'remaining': self.max_requests - len(user_queue),
            'reset_at': current_time + self.window_seconds,
            'retry_after': 0
        }
        
        return True, rate_limit_info
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get statistics for a specific user"""
        stats = self.user_stats[user_id].copy()
        current_queue_size = len(self.user_requests[user_id])
        
        stats.update({
            'current_requests_in_window': current_queue_size,
            'remaining_requests': max(0, self.max_requests - current_queue_size)
        })
        
        return stats
    
    def get_global_stats(self) -> Dict:
        """Get global rate limiting statistics"""
        total_users = len(self.user_stats)
        total_requests = sum(stats['total_requests'] for stats in self.user_stats.values())
        total_blocked = sum(stats['blocked_requests'] for stats in self.user_stats.values())
        
        active_users = len([uid for uid, queue in self.user_requests.items() if queue])
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_requests': total_requests,
            'blocked_requests': total_blocked,
            'success_rate': (total_requests - total_blocked) / total_requests if total_requests > 0 else 1.0,
            'max_requests_per_window': self.max_requests,
            'window_seconds': self.window_seconds
        }
    
    def reset_user(self, user_id: int):
        """Reset rate limiting for a specific user (admin function)"""
        if user_id in self.user_requests:
            self.user_requests[user_id].clear()
        if user_id in self.user_stats:
            self.user_stats[user_id] = {
                'total_requests': 0,
                'blocked_requests': 0, 
                'first_request': None,
                'last_request': None
            }
        logger.info(f"Rate limit reset for user {user_id}")
