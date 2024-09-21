from chroma.app.domain.chroma_collections import ChromaCollections
from utils.request_validator import validate_params
from flask import Blueprint, request, jsonify
import json

chroma_router = Blueprint('chroma', __name__, url_prefix='/chroma')
chroma_collections = ChromaCollections()


@chroma_router.get("/documents")
def execute_basic_chroma_query():
    request_data = json.loads(request.data.decode('utf-8'))
    search_text = request_data.get('search_text', False)
    category = request_data.get('category', False)
    collection_name = request_data.get('collection_name', False)

    if validate_params(
            collection_name, category, search_text):
        return jsonify(chroma_collections.execute_search_query(
            collection_name, category, search_text
        ))

    return jsonify({
        'STATE': 'Query failed',
        'DESCRIPTION': 'Please provide enough information to '
        'execute the query.'})


@chroma_router.post("/embed_document")
def process_pdf_file():

    request_data = json.loads(request.data.decode('utf-8'))
    file_path = request_data.get('file_path', False)
    categories = request_data.get('categories', False)
    collection_name = request_data.get('collection_name', False)

    if validate_params(
            file_path, categories, collection_name):
        return jsonify(chroma_collections.process_pdf_file(
            file_path, categories, collection_name
        ))

# TODO: add celery as async queue

# TODO: access pdf directory Try bind mounts

# TODO: Load pdf files from database into local file system
