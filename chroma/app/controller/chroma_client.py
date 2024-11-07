from chroma.app.task_executor import (chroma_search_query_task,
                                      chroma_embed_task,
                                      sse_stream)
from utils.request_validator import (validate_params, get_request_data)
from flask import Blueprint, request, jsonify, Response
from chroma_ms_config import Configuration
import json

chroma_router = Blueprint('chroma', __name__, url_prefix='/chroma')


@chroma_router.route('/task-status', methods=['POST'])
def receive_task_status():
    data = json.loads(request.data.decode('utf-8'))
    (task_status, task_result) = get_request_data(data,
                                                  'status',
                                                  'result')

    print(f"Received task status: {task_status}")
    print(f"Task result: {task_result}")

    return jsonify({"STATUS": task_status,
                    "RESPONSE_DATA": task_result})


@chroma_router.post("/documents")
def execute_basic_chroma_query():
    request_data = json.loads(request.data.decode('utf-8'))
    (user_query,
     category,
     collection_name,
     callback_url) = get_request_data(request_data,
                                      'user_query',
                                      'category',
                                      'collection_name',
                                      'callback_url')

    if validate_params(
            collection_name, category, user_query):
        task = chroma_search_query_task.apply_async(
            args=[collection_name, category, user_query],
            queue=Configuration.CHROMA_QUEUE)
        return Response(sse_stream(task.id), content_type='text/event-stream')

    return jsonify({
        'STATE': 'Query failed',
        'DESCRIPTION': 'Please provide enough information to '
                       'execute the query.'})


@chroma_router.post("/embed_document")
def process_pdf_file():
    request_data = json.loads(request.data.decode('utf-8'))

    file_path, categories, collection_name = get_request_data(
        request_data,
        'file_path',
        'categories',
        'collection_name')

    if validate_params(file_path, categories, collection_name):
        task = chroma_embed_task.apply_async(
            args=[collection_name, file_path, categories],
            queue=Configuration.CHROMA_QUEUE)
        return Response(sse_stream(task.id), content_type='text/event-stream')

@chroma_router.post("/form_embed_documen")
def form_process_pdf_file():
    uploaded_file = request.files.get('file')
    categories = request.form.get('categories')
    collection_name = request.form.get('collection_name')
    
    file_path = f"/tmp/{uploaded_file.filename}"
    uploaded_file.save(file_path)
    
    if validate_params(uploaded_file, categories, collection_name):
        task = chroma_embed_task.apply_async(
            args=[collection_name, file_path, categories, True],
            queue=Configuration.CHROMA_QUEUE)
        return Response(sse_stream(task.id), content_type='text/event-stream')
