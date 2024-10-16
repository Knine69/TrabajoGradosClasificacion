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
                # Once the result is available, stream it to the client and exit
                yield f"data: {result.decode('utf-8')}\n\n"
                break  # End the loop after sending the result

            time.sleep(2)  # Poll every 2 seconds
    except GeneratorExit:
        print_error(f"Client disconnected while waiting for task {task_id}",
                    app=Configuration.CHROMA_QUEUE)
    except Exception as e:
        print_error(f"Error during SSE streaming: {e}",
                    app=Configuration.CHROMA_QUEUE)
        yield f"data: Error while processing task {task_id}\n\n"


@celery.task(soft_time_limit=30, time_limit=50)
def execute_task(*data, function):
    return function(*data)


@celery.task(soft_time_limit=30, time_limit=50)
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

    result = ChromaCollections().process_pdf_file(
        file_path=file_path,
        collection_name=collection_name,
        categories=categories)

    task_id = chroma_embed_task.request.id
    _store_task_results(task_id, result)

    return result


@celery.task(time_limit=120)
def notify_task_completion(result, callback_url):
    response = requests.post(callback_url, json={
        'status': 'Completed',
        'result': result
    })

    if response.status_code != 200:
        print(f"Failed to notify callback URL: {callback_url}")


def _store_task_results(task_id, result) -> None:
    print_successful_message(
        message=f"Storing result of task: {task_id} on redis...",
        app=Configuration.CHROMA_QUEUE)

    redis_client.set(task_id, json.dumps(result))
