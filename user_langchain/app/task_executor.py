import time
import requests
import json
from user_langchain.celery_conf import celery
from user_langchain.app import redis_client
from user_langchain.app.domain.agent_invocations import LangchainAgent
from utils.outputs import print_console_message, OutputColors


def sse_stream(task_id):
    """Stream events to the client."""
    while True:
        result = redis_client.get(task_id)

        if result:
            yield f"data: {result.decode('utf-8')}\n\n"
            break

        time.sleep(2)  # Poll every 2 seconds


@celery.task
def execute_task(*data, function):
    return function(*data)


@celery.task
def langchain_agent_invocation_task(categories, documents):
    result = LangchainAgent().execute_agent_query(categories, documents)

    task_id = langchain_agent_invocation_task.request.id
    _store_task_results(task_id, result)

    return result


@celery.task
def notify_task_completion(result, callback_url):
    response = requests.post(callback_url, json={
        'status': 'Completed',
        'result': result
    })

    if response.status_code != 200:
        print(f"Failed to notify callback URL: {callback_url}")


def _store_task_results(task_id, result) -> None:
    print_console_message(
        message=f"Storing result of task: {task_id} on redis...",
        message_color=OutputColors.OKBLUE.value
    )
    redis_client.set(task_id, json.dumps(result))
