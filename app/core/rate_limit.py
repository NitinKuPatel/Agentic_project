from fastapi import HTTPException, status
import time
from app.infrastructure.cache.redis_client import redis_client
from app.observability.logging import logger

class RateLimiter:
    """
    Rolling window rate limiter using Redis.
    """
    def __init__(self, times: int = 10, seconds: int = 60):
        self.times = times
        self.seconds = seconds

    async def check_rate_limit(self, key: str):
        redis = redis_client.redis
        # Lua script for atomic rate limiting
        # 1. ZREMRANGEBYSCORE: Remove items older than window
        # 2. ZCARD: Count remaining items
        # 3. ZADD: Add current timestamp if under limit
        
        current_time = time.time()
        window_start = current_time - self.seconds
        
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await (pipe
                    .zremrangebyscore(key, 0, window_start)
                    .zcard(key)
                    .execute())
                
                # Result of ZCARD is at index 1
                usage_count = pipe.results()[1]
                
                if usage_count >= self.times:
                    logger.warning(f"Rate limit exceeded for {key}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later."
                    )
                
                # Add current request timestamp
                await redis.zadd(key, {str(current_time): current_time})
                # Set expiry on the key to autorotate cleanup
                await redis.expire(key, self.seconds + 1)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Rate limiter error: {e}", exc_info=True)
                # Fail open or closed? Here we fail open to avoid blocking legitimate traffic on redis error
                # In strict environments, fail closed.

# Dependency factory
def rate_limit(times: int = 60, seconds: int = 60):
    limiter = RateLimiter(times, seconds)
    async def wrapper(user_id: str = "anonymous"): # In real usage, inject user ID
        # Construct key: rate_limit:{user_id}
        key = f"rate_limit:{user_id}"
        await limiter.check_rate_limit(key)
    return wrapper
