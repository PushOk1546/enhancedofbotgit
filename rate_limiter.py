"""
Rate Limiter Module for Enhanced OF Bot
Implements rate limiting with Redis-like in-memory storage.
"""

import time
import asyncio
import logging
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting rules."""
    
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    cooldown_seconds: int = 300  # 5 minutes penalty
    

@dataclass
class UserLimitStatus:
    """Tracks rate limit status for a user."""
    
    user_id: int
    minute_requests: int = 0
    hour_requests: int = 0
    burst_count: int = 0
    last_request_time: float = field(default_factory=time.time)
    minute_reset_time: float = field(default_factory=time.time)
    hour_reset_time: float = field(default_factory=time.time)
    penalty_until: Optional[float] = None
    

class RateLimitRepository(ABC):
    """Abstract repository for rate limit data storage."""
    
    @abstractmethod
    async def get_user_status(self, user_id: int) -> Optional[UserLimitStatus]:
        """Get user rate limit status."""
        pass
    
    @abstractmethod
    async def save_user_status(self, status: UserLimitStatus) -> None:
        """Save user rate limit status."""
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> None:
        """Clean up expired rate limit data."""
        pass


class InMemoryRateLimitRepository(RateLimitRepository):
    """In-memory implementation of rate limit repository."""
    
    def __init__(self, cleanup_interval: int = 3600) -> None:
        """Initialize repository with cleanup interval."""
        self.storage: Dict[int, UserLimitStatus] = {}
        self.cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
    
    async def get_user_status(self, user_id: int) -> Optional[UserLimitStatus]:
        """Get user rate limit status from memory."""
        await self._cleanup_if_needed()
        return self.storage.get(user_id)
    
    async def save_user_status(self, status: UserLimitStatus) -> None:
        """Save user rate limit status to memory."""
        self.storage[status.user_id] = status
    
    async def cleanup_expired(self) -> None:
        """Remove expired entries from memory."""
        current_time = time.time()
        expired_users = []
        
        for user_id, status in self.storage.items():
            # Remove if no activity for 24 hours
            if current_time - status.last_request_time > 86400:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.storage[user_id]
        
        self._last_cleanup = current_time
        logger.info(f"Cleaned up {len(expired_users)} expired rate limit entries")
    
    async def _cleanup_if_needed(self) -> None:
        """Run cleanup if interval has passed."""
        if time.time() - self._last_cleanup > self.cleanup_interval:
            await self.cleanup_expired()


class RateLimiter:
    """Advanced rate limiter with multiple limits and burst protection."""
    
    def __init__(
        self,
        repository: RateLimitRepository,
        config: RateLimitConfig = None
    ) -> None:
        """Initialize rate limiter with dependency injection."""
        self.repository = repository
        self.config = config or RateLimitConfig()
        
    async def is_allowed(self, user_id: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user request is allowed.
        
        Returns:
            Tuple of (is_allowed, info_dict)
        """
        current_time = time.time()
        status = await self._get_or_create_status(user_id)
        
        # Check penalty period
        if status.penalty_until and current_time < status.penalty_until:
            return False, {
                'reason': 'penalty',
                'retry_after': status.penalty_until - current_time,
                'message': 'Rate limit exceeded. Try again later.'
            }
        
        # Reset counters if time windows have passed
        self._reset_counters_if_needed(status, current_time)
        
        # Check limits
        if not self._check_limits(status):
            # Apply penalty for exceeding limits
            status.penalty_until = current_time + self.config.cooldown_seconds
            await self.repository.save_user_status(status)
            
            return False, {
                'reason': 'rate_limit',
                'retry_after': self.config.cooldown_seconds,
                'message': 'Too many requests. Cooling down.'
            }
        
        # Update counters
        await self._update_counters(status, current_time)
        
        return True, {
            'remaining_minute': (
                self.config.requests_per_minute - status.minute_requests
            ),
            'remaining_hour': (
                self.config.requests_per_hour - status.hour_requests
            )
        }
    
    async def record_request(self, user_id: int) -> None:
        """Record a successful request for the user."""
        status = await self._get_or_create_status(user_id)
        status.last_request_time = time.time()
        await self.repository.save_user_status(status)
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get rate limit statistics for a user."""
        status = await self._get_or_create_status(user_id)
        current_time = time.time()
        
        return {
            'user_id': user_id,
            'minute_requests': status.minute_requests,
            'hour_requests': status.hour_requests,
            'burst_count': status.burst_count,
            'penalty_active': (
                status.penalty_until is not None and 
                current_time < status.penalty_until
            ),
            'penalty_remaining': (
                max(0, status.penalty_until - current_time) 
                if status.penalty_until else 0
            )
        }
    
    async def _get_or_create_status(self, user_id: int) -> UserLimitStatus:
        """Get existing status or create new one."""
        status = await self.repository.get_user_status(user_id)
        if status is None:
            status = UserLimitStatus(user_id=user_id)
        return status
    
    def _reset_counters_if_needed(
        self, 
        status: UserLimitStatus, 
        current_time: float
    ) -> None:
        """Reset counters if time windows have expired."""
        # Reset minute counter
        if current_time - status.minute_reset_time >= 60:
            status.minute_requests = 0
            status.minute_reset_time = current_time
        
        # Reset hour counter
        if current_time - status.hour_reset_time >= 3600:
            status.hour_requests = 0
            status.hour_reset_time = current_time
        
        # Reset burst counter (shorter window)
        if current_time - status.last_request_time >= 10:
            status.burst_count = 0
    
    def _check_limits(self, status: UserLimitStatus) -> bool:
        """Check if current request would exceed any limits."""
        return (
            status.minute_requests < self.config.requests_per_minute and
            status.hour_requests < self.config.requests_per_hour and
            status.burst_count < self.config.burst_limit
        )
    
    async def _update_counters(
        self, 
        status: UserLimitStatus, 
        current_time: float
    ) -> None:
        """Update request counters."""
        status.minute_requests += 1
        status.hour_requests += 1
        status.burst_count += 1
        status.last_request_time = current_time
        
        await self.repository.save_user_status(status)


class RateLimitMiddleware:
    """Middleware for applying rate limiting to bot handlers."""
    
    def __init__(self, rate_limiter: RateLimiter) -> None:
        """Initialize with rate limiter dependency."""
        self.rate_limiter = rate_limiter
    
    async def check_rate_limit(self, user_id: int) -> Tuple[bool, str]:
        """
        Check rate limit and return result.
        
        Returns:
            Tuple of (is_allowed, message)
        """
        try:
            is_allowed, info = await self.rate_limiter.is_allowed(user_id)
            
            if not is_allowed:
                reason = info.get('reason', 'unknown')
                retry_after = info.get('retry_after', 0)
                
                if reason == 'penalty':
                    message = (
                        f"⏰ Превышен лимит запросов. "
                        f"Попробуйте через {int(retry_after)} секунд."
                    )
                else:
                    message = "⚡ Слишком много запросов. Подождите немного."
                
                return False, message
            
            # Record successful check
            await self.rate_limiter.record_request(user_id)
            return True, ""
            
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {e}")
            # In case of error, allow the request but log it
            return True, ""


# Global instances for easy import
default_config = RateLimitConfig(
    requests_per_minute=30,     # Conservative for OF bot
    requests_per_hour=500,      # Reasonable for active users
    burst_limit=5,              # Prevent spam
    cooldown_seconds=180        # 3 minute penalty
)

default_repository = InMemoryRateLimitRepository()
default_rate_limiter = RateLimiter(default_repository, default_config)
rate_limit_middleware = RateLimitMiddleware(default_rate_limiter) 