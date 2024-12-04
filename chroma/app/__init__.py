import redis
from chroma_ms_config import Configuration

redis_client = redis.StrictRedis.from_url(Configuration.CELERY_RESULT_BACKEND)
loaded_collections = {}


def test_redis_connection():
    try:
        client = redis.StrictRedis(host='localhost', port=6379, db=0)
        response = client.ping()
        if response:
            print("Successfully connected to Redis!")
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")


test_redis_connection()
__all__ = ["redis_client", "loaded_collections"]

