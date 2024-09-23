from flask import Flask
from chroma.app_config import Configuration
from chroma.app.controller.chroma_client import chroma_router
from chroma.celery_conf import celery, celery_instantiation
import redis


def test_redis_connection():
    try:
        client = redis.StrictRedis(host='localhost', port=6379, db=0)
        response = client.ping()
        if response:
            print("Successfully connected to Redis!")
    except redis.ConnectionError as e:
        print(f"Redis connection error: {e}")


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration())
    celery_instantiation(app)
    app.register_blueprint(chroma_router)
    test_redis_connection()
    return app
