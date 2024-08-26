from langchain.tools import tool


@tool
def check_word_length(word: str) -> int:
    """Takes a word and checks its length."""
    result = len(word.replace("'", "").replace('"', ''))
    return result


tools = [check_word_length]

# TODO: create a tool which calls chroma query
