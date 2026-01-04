import redis.asyncio as redis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

    async def get(self, key: str):
        return await self.redis.get(key)
    
    async def set(self, key: str, value: str, expire: int = None):
        if expire:
            await self.redis.set(key, value, ex=expire)
        else:
            await self.redis.set(key, value)
            
    async def close(self):
        await self.redis.close()

redis_client = RedisClient()

async def get_redis():
    return redis_client
