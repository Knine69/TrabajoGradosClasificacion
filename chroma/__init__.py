from flask import Flask
from chroma.app.controller.chroma_client import chroma_router


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(chroma_router)
    return app

