from chroma.flask.domain.chroma_collections import ChromaCollections
from utils.request_validator import validate_params
from flask import Blueprint, request, jsonify

chroma_router = Blueprint('chroma', __name__, url_prefix='/chroma')
chroma_collections = ChromaCollections()


@chroma_router.get("/documents")
def execute_basic_chroma_query():
    collection_name = request.args.get('collection')
    category = request.args.get('category')
    search_text = request.args.get('search_text')

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
    file_path = request.args.get('file_path')
    categories = request.args.getlist('categories')
    collection_name = request.args.get('collection_name')

    if validate_params(
            file_path, categories, collection_name):
        return jsonify(chroma_collections.process_pdf_file(
            file_path, categories, collection_name
        ))

# TODO: access pdf directory Try bind mounts

# TODO: Load pdf files from database into local file system
