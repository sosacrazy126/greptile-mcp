"""
Rate limiting and throttling utilities for Greptile MCP Server.

This module provides rate limiting functionality to prevent API abuse
and ensure fair usage of the Greptile API.
"""

import os
import time
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from src.logging_config import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_limit: int = 10
    cooldown_seconds: float = 1.0


@dataclass
class RateLimitState:
    """State tracking for rate limiting."""
    minute_requests: deque = field(default_factory=deque)
    hour_requests: deque = field(default_factory=deque)
    last_request_time: float = 0.0
    consecutive_requests: int = 0


class RateLimiter:
    """
    Token bucket rate limiter with multiple time windows.
    
    Implements rate limiting with:
    - Per-minute limits
    - Per-hour limits  
    - Burst protection
    - Adaptive cooldown
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.states: Dict[str, RateLimitState] = defaultdict(RateLimitState)
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """
        Check if a request is allowed under rate limits.
        
        Args:
            identifier: Unique identifier for the client (e.g., session_id, IP)
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        async with self._lock:
            current_time = time.time()
            state = self.states[identifier]
            
            # Clean up old requests
            self._cleanup_old_requests(state, current_time)
            
            # Check per-minute limit
            if len(state.minute_requests) >= self.config.requests_per_minute:
                retry_after = 60 - (current_time - state.minute_requests[0])
                logger.warning(
                    f"Rate limit exceeded (per-minute)",
                    identifier=identifier,
                    requests_in_minute=len(state.minute_requests),
                    limit=self.config.requests_per_minute,
                    retry_after=retry_after
                )
                return False, retry_after
            
            # Check per-hour limit
            if len(state.hour_requests) >= self.config.requests_per_hour:
                retry_after = 3600 - (current_time - state.hour_requests[0])
                logger.warning(
                    f"Rate limit exceeded (per-hour)",
                    identifier=identifier,
                    requests_in_hour=len(state.hour_requests),
                    limit=self.config.requests_per_hour,
                    retry_after=retry_after
                )
                return False, retry_after
            
            # Check burst limit
            time_since_last = current_time - state.last_request_time
            if time_since_last < self.config.cooldown_seconds:
                state.consecutive_requests += 1
                if state.consecutive_requests > self.config.burst_limit:
                    retry_after = self.config.cooldown_seconds
                    logger.warning(
                        f"Burst limit exceeded",
                        identifier=identifier,
                        consecutive_requests=state.consecutive_requests,
                        burst_limit=self.config.burst_limit,
                        retry_after=retry_after
                    )
                    return False, retry_after
            else:
                state.consecutive_requests = 0
            
            # Record the request
            state.minute_requests.append(current_time)
            state.hour_requests.append(current_time)
            state.last_request_time = current_time
            
            logger.debug(
                f"Request allowed",
                identifier=identifier,
                requests_in_minute=len(state.minute_requests),
                requests_in_hour=len(state.hour_requests)
            )
            
            return True, None
    
    def _cleanup_old_requests(self, state: RateLimitState, current_time: float):
        """Remove requests older than the time windows."""
        # Clean minute window
        while state.minute_requests and current_time - state.minute_requests[0] > 60:
            state.minute_requests.popleft()
        
        # Clean hour window
        while state.hour_requests and current_time - state.hour_requests[0] > 3600:
            state.hour_requests.popleft()
    
    async def get_rate_limit_status(self, identifier: str) -> Dict[str, any]:
        """Get current rate limit status for an identifier."""
        async with self._lock:
            current_time = time.time()
            state = self.states[identifier]
            self._cleanup_old_requests(state, current_time)
            
            return {
                "requests_in_minute": len(state.minute_requests),
                "requests_in_hour": len(state.hour_requests),
                "minute_limit": self.config.requests_per_minute,
                "hour_limit": self.config.requests_per_hour,
                "consecutive_requests": state.consecutive_requests,
                "burst_limit": self.config.burst_limit,
                "time_since_last_request": current_time - state.last_request_time
            }
    
    async def reset_limits(self, identifier: str):
        """Reset rate limits for a specific identifier."""
        async with self._lock:
            if identifier in self.states:
                del self.states[identifier]
                logger.info(f"Rate limits reset for identifier: {identifier}")


class AdaptiveRateLimiter(RateLimiter):
    """
    Adaptive rate limiter that adjusts limits based on API response patterns.
    
    Reduces limits when API errors are detected and gradually increases
    them when the API is healthy.
    """
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.success_counts: Dict[str, int] = defaultdict(int)
        self.adaptive_multipliers: Dict[str, float] = defaultdict(lambda: 1.0)
    
    async def record_api_response(self, identifier: str, success: bool, status_code: int = None):
        """Record API response to adjust rate limits adaptively."""
        async with self._lock:
            if success:
                self.success_counts[identifier] += 1
                # Gradually increase limits on success
                if self.success_counts[identifier] % 10 == 0:
                    self.adaptive_multipliers[identifier] = min(
                        self.adaptive_multipliers[identifier] * 1.1,
                        2.0  # Max 2x the base limit
                    )
                    logger.debug(
                        f"Increased rate limit multiplier",
                        identifier=identifier,
                        multiplier=self.adaptive_multipliers[identifier]
                    )
            else:
                self.error_counts[identifier] += 1
                # Decrease limits on errors
                if status_code and status_code == 429:  # Too Many Requests
                    self.adaptive_multipliers[identifier] *= 0.5
                elif status_code and status_code >= 500:  # Server errors
                    self.adaptive_multipliers[identifier] *= 0.7
                else:  # Other errors
                    self.adaptive_multipliers[identifier] *= 0.8
                
                self.adaptive_multipliers[identifier] = max(
                    self.adaptive_multipliers[identifier],
                    0.1  # Min 10% of base limit
                )
                
                logger.warning(
                    f"Decreased rate limit multiplier due to API error",
                    identifier=identifier,
                    multiplier=self.adaptive_multipliers[identifier],
                    status_code=status_code
                )
    
    async def check_rate_limit(self, identifier: str) -> Tuple[bool, Optional[float]]:
        """Check rate limits with adaptive adjustments."""
        # Apply adaptive multiplier to limits
        multiplier = self.adaptive_multipliers[identifier]
        original_config = self.config
        
        # Temporarily adjust config
        self.config = RateLimitConfig(
            requests_per_minute=int(original_config.requests_per_minute * multiplier),
            requests_per_hour=int(original_config.requests_per_hour * multiplier),
            burst_limit=max(1, int(original_config.burst_limit * multiplier)),
            cooldown_seconds=original_config.cooldown_seconds / multiplier
        )
        
        try:
            result = await super().check_rate_limit(identifier)
            return result
        finally:
            # Restore original config
            self.config = original_config


# Global rate limiter instance
_global_rate_limiter: Optional[AdaptiveRateLimiter] = None


def get_rate_limiter() -> AdaptiveRateLimiter:
    """Get the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        config = RateLimitConfig(
            requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            burst_limit=int(os.getenv("RATE_LIMIT_BURST", "10")),
            cooldown_seconds=float(os.getenv("RATE_LIMIT_COOLDOWN", "1.0"))
        )
        _global_rate_limiter = AdaptiveRateLimiter(config)
        logger.info("Rate limiter initialized", config=config.__dict__)
    
    return _global_rate_limiter


@asynccontextmanager
async def rate_limited_request(identifier: str):
    """
    Context manager for rate-limited requests.
    
    Usage:
        async with rate_limited_request("session_123"):
            # Make API call
            result = await api_call()
    """
    rate_limiter = get_rate_limiter()
    
    # Check rate limit
    allowed, retry_after = await rate_limiter.check_rate_limit(identifier)
    
    if not allowed:
        logger.warning(
            f"Request blocked by rate limiter",
            identifier=identifier,
            retry_after=retry_after
        )
        raise RateLimitExceeded(f"Rate limit exceeded. Retry after {retry_after:.1f} seconds")
    
    success = False
    status_code = None
    
    try:
        yield
        success = True
    except Exception as e:
        # Try to extract status code from HTTP exceptions
        if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
            status_code = e.response.status_code
        raise
    finally:
        # Record the API response for adaptive rate limiting
        await rate_limiter.record_api_response(identifier, success, status_code)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


# Utility functions
async def check_rate_limit(identifier: str) -> bool:
    """Simple rate limit check."""
    rate_limiter = get_rate_limiter()
    allowed, _ = await rate_limiter.check_rate_limit(identifier)
    return allowed


async def get_rate_limit_info(identifier: str) -> Dict[str, any]:
    """Get rate limit information for debugging."""
    rate_limiter = get_rate_limiter()
    return await rate_limiter.get_rate_limit_status(identifier)
