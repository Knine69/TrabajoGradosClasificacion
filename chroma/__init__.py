from flask import Flask
from chroma.app_config import Configuration
from chroma.app.controller.chroma_client import chroma_router
from chroma.celery_conf import celery, celery_instantiation


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration())
    celery_instantiation(app)
    app.register_blueprint(chroma_router)

    return app
