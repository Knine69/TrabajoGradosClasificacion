import pytest

from unittest.mock import call, patch, MagicMock, ANY
from user_langchain.prompt import parser
from langchain_community.llms import Ollama
from langchain_ms_config import Configuration
from user_langchain.app.domain.chain_invocations import LangchainChain
from pydantic import ValidationError, BaseModel
from utils.outputs import OutputColors

@pytest.fixture
def langchain_chain():
    return LangchainChain()

def test_initialization(langchain_chain):
    # Chain itself can't be tested as type is ambiguous
    assert isinstance(langchain_chain.llm_model, Ollama)
    

def test_preprocess_json_string():
    input_str = '{"key": None}'
    expected_output = '{"key": null}'
    assert LangchainChain.preprocess_json_string(input_str) == expected_output


@patch('utils.outputs.print_console_message')
@patch('user_langchain.app.domain.chain_invocations.LangchainChain._invoke_query')
def test_execute_chain_query_success(mock_invoke_query: MagicMock,
                                     mock_console_message: MagicMock,
                                     langchain_chain):
    mock_invoke_query.return_value = {
        "STATE": False,
        "DESCRIPTION": "Too many failed attempts"}
    
    result = langchain_chain.execute_chain_query([], ["Some data for RAG"], "What is an action?")
    
    assert result['STATE'] is False
    assert result['DESCRIPTION'] == 'Too many failed attempts'
    
    mock_console_message.assert_any_call(
        message=ANY,
        message_color=OutputColors.WARNING.value,
        app=Configuration.LANGCHAIN_QUEUE
    )
    
    mock_console_message.assert_any_call(
        message="Query failed: Too many failed attempt",
        message_color=OutputColors.FAIL.value,
        app=Configuration.LANGCHAIN_QUEUE
    )
    
    
@patch('utils.outputs.print_console_message')
@patch('utils.outputs.print_error')
@patch('user_langchain.app.domain.chain_invocations.LangchainChain._invoke_query')
def test_execute_chain_query_success(mock_invoke_query: MagicMock,
                                     mock_print_error: MagicMock,
                                     mock_print_method: MagicMock,
                                     langchain_chain):
    mock_invoke_query.return_value = {
        "STATE": True,
        "QUERY_MADE": "What is an action?",
        "RESPONSE": '{"answer": "An action is..."}'
    }
    
    result = langchain_chain.execute_chain_query([], ["Some data for RAG"], "What is an action?")
    
    assert result['STATE'] is True
    assert result['RESPONSE'] == '{"answer": "An action is..."}'
    mock_print_method.assert_called()
    mock_print_error.assert_not_called()


def test_invoke_query_failed_exception(langchain_chain):
    with patch('utils.outputs.print_console_message') as mock_console_message:

        # Mock executor and invoke method
        mock_executor = MagicMock()
        mock_executor.invoke.side_effect = Exception("Test exception")

        # Call the _invoke_query method
        result = langchain_chain._invoke_query(
            mock_executor,
            {"question": "What is an action?", "references": []},
        )

        # Assert that print_console_message was called by print_error
        mock_console_message.assert_any_call(
            message='Something failed: Test exception',
            message_color=OutputColors.FAIL.value,
            app=Configuration.LANGCHAIN_QUEUE
        )
        
        mock_console_message.assert_any_call(
            message=ANY,
            message_color=OutputColors.WARNING.value,
            app=Configuration.LANGCHAIN_QUEUE
        )
        
        
        
class ExampleModel(BaseModel):
    field: str
    
    
def test_invoke_query_validation_error_exception(langchain_chain):
    with patch('utils.outputs.print_console_message') as mock_console_message:
        
        try:
            ExampleModel(field=123)
        except ValidationError as e:
            mock_validation_error = e
        
        # Mock executor and invoke method
        mock_executor = MagicMock()
        mock_executor.invoke.side_effect = mock_validation_error

        # Call the _invoke_query method
        result = langchain_chain._invoke_query(
            mock_executor,
            {"question": "What is an action?", "references": []},
        )

        # Assert that print_console_message was called by print_error
        mock_console_message.assert_any_call(
            message=ANY,
            message_color=OutputColors.FAIL.value,
            app=Configuration.LANGCHAIN_QUEUE
        )
        
        mock_console_message.assert_any_call(
            message=ANY,
            message_color=OutputColors.WARNING.value,
            app=Configuration.LANGCHAIN_QUEUE
        )
