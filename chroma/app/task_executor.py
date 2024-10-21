import time
import requests
import json
from chroma.celery_conf import celery
from chroma.app import redis_client
from chroma.app.domain.chroma_collections import ChromaCollections
from utils.outputs import print_successful_message, print_error
from chroma_ms_config import Configuration


def sse_stream(task_id):
    """Stream events to the client."""
    try:
        while True:
            # Poll Redis for task result
            result = redis_client.get(task_id)

            if result:
                state = result.get('state')

                if state == 'ERROR':
                    yield f"data: {json.dumps({'state': 'ERROR', 'message': result.get('result')})}\n\n"
                else:
                    yield f"data: {json.dumps({'state': 'SUCCESS', 'result': result.get('result')})}\n\n"
                break

            time.sleep(2)
    except GeneratorExit:
        print_error(f"Client disconnected while waiting for task {task_id}",
                    app=Configuration.CHROMA_QUEUE)
    except Exception as e:
        print_error(f"Error during SSE streaming: {e}",
                    app=Configuration.CHROMA_QUEUE)
        yield f"data: Error while processing task {task_id}\n\n"


def error_handler(task_id, exc):
    print_error(message=f'{task_id} - Something went wrong: {exc}',
                app=Configuration.CHROMA_QUEUE)
    redis_client.set(task_id,
                     json.dumps({'state': 'ERROR', 'result': exc}))


@celery.task(time_limit=120)
def chroma_search_query_task(collection_name, category, user_query):

    task_id = chroma_search_query_task.request.id
    result = ChromaCollections().execute_search_query(collection_name,
                                                      category,
                                                      user_query,
                                                      task_id)

    _store_task_results(task_id, result)

    return result


@celery.task(time_limit=240)
def chroma_embed_task(collection_name, file_path, categories):

    task_id = chroma_embed_task.request.id
    
    try:
        result = ChromaCollections().process_pdf_file(
            file_path=file_path,
            collection_name=collection_name,
            categories=categories)
        
        _store_task_results(task_id, result)
    except Exception as exc:
        error_handler(task_id, str(exc))
        return None

    return result


def _store_task_results(task_id, result) -> None:
    print_successful_message(
        message=f"Storing result of task: {task_id} on redis...",
        app=Configuration.LANGCHAIN_QUEUE)
    redis_client.set(task_id,
                     json.dumps({'state': 'SUCCESS', 'result':json.dumps(result)}))
