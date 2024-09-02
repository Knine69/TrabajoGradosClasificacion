from langchain.tools import tool
from tools import chroma_client


@tool
def check_word_length(word: str) -> int:
    """Takes a word and checks its length."""
    result = len(word.replace("'", "").replace('"', ''))
    return result


# TODO: Modify tool to simply categorize information retrieved from database

@tool
def perform_chroma_query(collection: str, categories: list[str]) -> bool:
    """Takes an input text and queries a chroma database"""
    result = chroma_client.execute_basic_chroma_query(collection, categories)
    print(f"Result: {result}")
    return True if result else False


tools = [check_word_length, perform_chroma_query]

