from flask import Flask
from user_langchain.flask.controller.agent import langchain_router


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(langchain_router)
    return app