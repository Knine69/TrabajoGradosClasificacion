from flask import Flask
from chroma.flask.controller.chroma_client import  chroma_router

loaded_collections = {}
__all__ = ['loaded_collections']


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(chroma_router)
    return app
