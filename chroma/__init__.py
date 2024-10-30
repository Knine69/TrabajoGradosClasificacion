from flask import Flask
from flask_cors import CORS
from chroma_ms_config import Configuration
from chroma.app.controller.chroma_client import chroma_router
from chroma.celery_conf import celery_instantiation



def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Configuration())
    celery_instantiation(app)
    app.register_blueprint(chroma_router)
    CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
    return app
