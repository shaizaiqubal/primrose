import redis
from backend.app.config import(
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    REDIS_USER
)

cache = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    username=REDIS_USER,
    password=REDIS_PASSWORD,
    decode_responses=True
)

TTL = 3600