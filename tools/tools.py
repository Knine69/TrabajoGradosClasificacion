from langchain.tools import tool


@tool
def check_word_length(word: str) -> int:
    """Takes a word and checks its length."""
    result = len(word.replace("'", "").replace('"', ''))
    return result


# TODO: Modify tool to simply categorize information retrieved from database

@tool
def perform_chroma_query(categories: list[str]) -> bool:
    """Takes an input text and queries a chroma database"""
    return True


tools = [check_word_length, perform_chroma_query]
