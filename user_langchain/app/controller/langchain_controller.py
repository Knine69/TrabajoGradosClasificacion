import json
from flask import Blueprint, request, jsonify, Response
from utils.request_validator import (validate_params, get_request_data)
from user_langchain.app.task_executor import (langchain_agent_invocation_task,
                                              sse_stream)
from langchain_ms_config import Configuration

langchain_router = Blueprint('langchain',
                             __name__,
                             url_prefix='/langchain')


@langchain_router.post("/search")
def search_query():
    request_data = json.loads(request.data.decode('utf-8'))

    (categories,
     documents,
     user_query,
     task_id) = get_request_data(request_data,
                                 'categories',
                                 'documents',
                                 'user_query',
                                 'task_id')

    if validate_params(categories, documents):
        task = langchain_agent_invocation_task.apply_async(
            args=[categories, documents, user_query],
            task_id=task_id,
            queue=Configuration.LANGCHAIN_QUEUE)
        return Response(sse_stream(task.id), content_type='text/event-stream')

    return jsonify({
        "STATE": "ERROR",
        "DESCRIPTION": "Please provide the required information to query."
    })
