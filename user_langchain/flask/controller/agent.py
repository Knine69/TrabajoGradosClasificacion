from flask import Blueprint, request, jsonify
from utils.request_validator import validate_params
from user_langchain.flask.domain.agent_invocations import LangchainAgent

langchain_router = Blueprint('langchain',
                             __name__,
                             url_prefix='/langchain')
langchain_agent = LangchainAgent()


@langchain_router.post("/search")
def search_query():
    categories = request.args.getlist('categories')
    if validate_params(categories):
        return jsonify(langchain_agent.execute_agent_query(categories))

    return jsonify({
        "STATE": "ERROR",
        "DESCRIPTION": "Please provide the required information to query."
    })


if __name__ == "__main__":
    agent = LangchainAgent()
    agent.execute_agent_query()
