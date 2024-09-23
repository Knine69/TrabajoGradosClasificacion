from chroma.app.domain.chroma_collections import ChromaCollections
from chroma.app.domain.task_executor import (chroma_search_query_task,
                                             notify_task_completion)
from utils.request_validator import validate_params
from flask import Blueprint, request, jsonify
import json

chroma_router = Blueprint('chroma', __name__, url_prefix='/chroma')
chroma_collections = ChromaCollections()


@chroma_router.route('/task-status', methods=['POST'])
def receive_task_status():
    data = json.loads(request.data.decode('utf-8'))
    (task_status, task_result) = _get_request_data(data,
                                                   'status',
                                                   'result')

    print(f"Received task status: {task_status}")
    print(f"Task result: {task_result}")

    return jsonify({"STATUS": task_status,
                    "RESPONSE_DATA": task_result})


@chroma_router.get("/documents")
def execute_basic_chroma_query():
    request_data = json.loads(request.data.decode('utf-8'))
    (search_text,
     category,
     collection_name,
     callback_url) = _get_request_data(request_data,
                                       'search_text',
                                       'category',
                                       'collection_name',
                                       'callback_url')

    print(f'Received params: {search_text}\n{category}\n{collection_name}\n{callback_url}')

    if validate_params(
            collection_name, category, search_text):
        print("PARAMS VALIDATED, ENTERING TASK INITIALIZATION")
        task = chroma_search_query_task.apply_async(
            args=[collection_name, category, search_text],
            link=notify_task_completion.s(callback_url))
        return jsonify({"task_id": task.id, "status": "Task submitted"}), 202

    return jsonify({
        'STATE': 'Query failed',
        'DESCRIPTION': 'Please provide enough information to '
                       'execute the query.'})


@chroma_router.post("/embed_document")
def process_pdf_file():
    request_data = json.loads(request.data.decode('utf-8'))

    file_path, categories, collection_name = _get_request_data(
        request_data,
        'file_path',
        'categories',
        'collection_name')

    if validate_params(
            file_path, categories, collection_name):
        return jsonify(chroma_collections.process_pdf_file(
            file_path, categories, collection_name
        ))


def _get_request_data(request_data, *names):
    return tuple(
        request_data.get(
            name,
            'http://localhost:5000/chroma/task-status' if name == 'callback_url'
            else False)
        for name in names
    )


# TODO: add celery as async queue, implement webhook callbacks

# TODO: access pdf directory Try bind mounts

# TODO: Load pdf files from database into local file system
