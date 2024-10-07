from flask import Flask
from app_config import Configuration
from user_langchain.celery_conf import celery_instantiation, celery
from user_langchain.app.controller.langchain_controller import langchain_router


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration())
    celery_instantiation(app)
    app.register_blueprint(langchain_router)
    return app


