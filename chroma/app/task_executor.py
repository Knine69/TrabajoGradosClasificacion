import time
import json
import gc
import os

from chroma.celery_conf import celery
from chroma.app import redis_client
from chroma.app.domain.chroma_collections import ChromaCollections
from utils.outputs import print_successful_message, print_error
from chroma_ms_config import Configuration
from billiard.exceptions import TimeLimitExceeded


def sse_stream(task_id):
    """Stream events to the client."""
    try:
        while True:
            # Poll Redis for task result
            result = redis_client.get(task_id)
            if result:
                decoded_result = json.loads(result.decode('utf-8'))
                state = decoded_result.get('state')
                inner_result = json.loads(decoded_result['result'])
                if state == 'ERROR':
                    yield f"data: {json.dumps({'state': 'ERROR', 'message': inner_result})}\n\n"
                else:
                    yield f"data: {json.dumps({'state': 'SUCCESS', 'result': inner_result})}\n\n"
                    
                gc.collect()
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


@celery.task()
def chroma_search_query_task(collection_name, category, user_query):

    task_id = chroma_search_query_task.request.id
    
    try:
        result = ChromaCollections().execute_search_query(collection_name,
                                                        category,
                                                        user_query,
                                                        task_id)

        _store_task_results(task_id, result)
        print_successful_message(app=Configuration.CHROMA_QUEUE,
                                 message=f"Task result: {result}")
        _store_task_results(task_id, result)
    except Exception as exc:
        error_handler(task_id, str(exc))
        return None
    
    except TimeLimitExceeded:
        error_handler(task_id, "Task exceeded the time alloted to be used.")
        return None

    return result


@celery.task(soft_time_limit=500)
def chroma_embed_task(collection_name, file_path, categories, isForm=False):

    task_id = chroma_embed_task.request.id
    
    try:
        result = ChromaCollections().process_pdf_file(
            file_path=file_path,
            collection_name=collection_name,
            categories=categories)
        
        _store_task_results(task_id, result)
    except TimeLimitExceeded:
        error_handler(task_id, "Task exceeded the time alloted to be used.")
        return None
    except Exception as exc:
        error_handler(task_id, str(exc))
        return None
    finally:
        if isForm:
            if os.path.exists(file_path):
                os.remove(file_path)

    return result


def _store_task_results(task_id, result) -> None:
    print_successful_message(
        message=f"Storing result of task: {task_id} on redis...",
        app=Configuration.LANGCHAIN_QUEUE)
    redis_client.set(task_id,
                     json.dumps({'state': 'SUCCESS', 'result':json.dumps(result)}))
