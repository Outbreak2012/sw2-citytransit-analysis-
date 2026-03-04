import redis
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class RedisConnection:
    """Redis cache connection"""
    
    def __init__(self):
        self.client = None
    
    def connect(self):
        """Connect to Redis"""
        try:
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
            logger.info("✅ Connected to Redis")
            return self.client
        except Exception as e:
            logger.error(f"❌ Error connecting to Redis: {e}")
            raise
    
    def get(self, key: str):
        """Get value from cache"""
        if not self.client:
            self.connect()
        value = self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value, ttl: int = None):
        """Set value in cache"""
        if not self.client:
            self.connect()
        ttl = ttl or settings.CACHE_TTL
        self.client.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        """Delete key from cache"""
        if not self.client:
            self.connect()
        self.client.delete(key)
    
    def disconnect(self):
        """Disconnect from Redis"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from Redis")


# Global connection instance
redis_conn = RedisConnection()


def get_redis():
    """Get Redis connection"""
    if not redis_conn.client:
        redis_conn.connect()
    return redis_conn.client
