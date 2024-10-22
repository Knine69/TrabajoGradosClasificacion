import time
import json
from user_langchain.celery_conf import celery
from user_langchain.app import redis_client
from user_langchain.app.domain.chain_invocations import LangchainChain
from utils.outputs import print_successful_message, print_error
from langchain_ms_config import Configuration
from billiard.exceptions import TimeLimitExceeded


def sse_stream(task_id):
    """Stream events to the client."""
    try:
        while True:
            result = redis_client.get(task_id)

            if result:
                decoded_result = json.loads(result.decode('utf-8'))
                state = decoded_result.get('state')

                if state == 'ERROR':
                    yield f"data: {json.dumps({'STATE': 'ERROR', 'DESCRIPTION': decoded_result.get('result')})}\n\n"
                else:
                    yield f"data: {json.dumps({'STATE': 'SUCCESS', 'DESCRIPTION': decoded_result.get('result')})}\n\n"
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
                app=Configuration.LANGCHAIN_QUEUE)
    redis_client.set(task_id,
                     json.dumps({'state': 'ERROR', 'result': exc}))


@celery.task(time_limit=220)
def langchain_agent_invocation_task(categories, documents, user_query):
    task_id = langchain_agent_invocation_task.request.id
    
    try:
        result = LangchainChain().execute_chain_query(categories,
                                                  documents,
                                                  user_query)
        print_successful_message(app=Configuration.LANGCHAIN_QUEUE,
                                 message=f"Task result: {result}")
        _store_task_results(task_id, result)
    except Exception as exc:
        error_handler(task_id, str(exc))
        return None
    except TimeLimitExceeded as exc:
        error_handler(task_id, str(exc))
        return None

    return result


def _store_task_results(task_id, result) -> None:
    print_successful_message(
        message=f"Storing result of task: {task_id} on redis...",
        app=Configuration.LANGCHAIN_QUEUE)
    redis_client.set(task_id,
                     json.dumps({'state': 'SUCCESS', 'result':json.dumps(result)}))
