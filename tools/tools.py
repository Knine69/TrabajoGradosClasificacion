from langchain.tools import tool


@tool
def check_word_length(word: str) -> int:
    """Takes a word and checks its length."""
    return len(word)


tools = [check_word_length]
