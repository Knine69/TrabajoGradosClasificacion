import pytest
import time
import torch
from chromadb.errors import InvalidCollectionException
from unittest.mock import patch, MagicMock, ANY
from chroma.app.domain.chroma_collections import ChromaCollections, chunk_text
from chromadb.api.types import GetResult, QueryResult
from utils.outputs import OutputColors
from langchain_ms_config import Configuration


@pytest.fixture(scope='session', autouse=True)
def mock_collections():
    with patch('chroma.app.domain.chroma_collections.chromadb') as mock_chromadb:
        # Mock HttpClient specifically to prevent connection attempts
        mock_http_client = MagicMock()
        mock_chromadb.HttpClient.return_value = mock_http_client
        collections = ChromaCollections()

        yield collections


@pytest.fixture
def mock_embedder_function():
    with patch('chroma.app.domain.chroma_collections.AutoTokenizer') as mock_tokenizer, \
         patch('chroma.app.domain.chroma_collections.AutoModel') as mock_model, \
         patch('chroma.app.domain.chroma_collections.torch') as mock_torch:

        # Mock tokenizer behavior
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer_instance.return_value = {
            'input_ids': MagicMock(),
            'attention_mask': MagicMock()
        }
        
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        # Mock model behavior
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance

        # Create a mock tensor with the expected shape
        mock_last_hidden_state = torch.rand(64, 512, 768)  # 64 batches, 512 tokens, 768 embedding size
        mock_output = MagicMock()
        mock_output.last_hidden_state = mock_last_hidden_state
        mock_model_instance.return_value = mock_output

        # Mock torch.mean to return a mock tensor
        mock_torch.mean.return_value = torch.rand(64, 768)  # 64 documents, 768 embedding size

        yield mock_tokenizer, mock_model, mock_torch


def test_chunk_text():
    expected_response = (["Some filler", "text to", "be chunked"], [])
    chunks, ids = chunk_text(text="Some filler text to be chunked", max_chunk_length=2)
    assert expected_response[0] == chunks

def test_chroma_collections_init(mock_collections):
    assert isinstance(mock_collections._chroma_client, MagicMock)


def test_embedder_function_call(mock_embedder_function):
    # Initialize EmbedderFunction
    embedder = ChromaCollections.EmbedderFunction()

    # Mock inputs
    doc_input = [f"This is a test document: {i}" for i in range(64)]
    
    # Call the embedder
    embeddings = embedder(doc_input)

    # Assertions
    assert isinstance(embeddings, list)
    assert len(embeddings) == len(doc_input)

    # Check if tokenizer and model were called as expected
    mock_tokenizer, mock_model, mock_torch = mock_embedder_function
    mock_tokenizer.from_pretrained.assert_called_with("bert-base-multilingual-cased")
    mock_model.from_pretrained.assert_called_with("bert-base-multilingual-cased")


def test_create_metadata_object(mock_collections):
    categories_list = ['CONTROL', 'QUIMICA']
    expected_result = {
        'control': True,
        'quimica': True
    }
    result: dict = mock_collections.create_metadata_object(categories_list)
    
    assert len(categories_list) == len(result.keys())
    assert expected_result == result


@patch('utils.outputs.print_console_message')
@patch("chroma.app.domain.chroma_collections.Collection")
def test_update_loaded_data(collection: MagicMock, console_print_mock: MagicMock, mock_collections):
    
    expected_response = {
        "ids": [],
        "embeddings":[],
        "documents":[],
        "uris":[""],
        "data":"",
        "metadatas":[""],
        "included":"documents"
    }
    
    mocked_response = GetResult(
        ids=[],
        embeddings=[],
        documents=[],
        uris=[""],
        data="",
        metadatas=[""],
        included="documents"
    )
    
    collection.get.return_value = mocked_response
    
    result = mock_collections.update_loaded_data(collection, "control")
    
    assert result == expected_response
    collection.get.assert_called()
    
    console_print_mock.assert_any_call(
        message=ANY,
        message_color=OutputColors.WARNING.value,
        app=Configuration.CHROMA_QUEUE
    )
    
    
@patch('utils.outputs.print_console_message')
@patch("chroma.app.domain.chroma_collections.Collection")
def test_update_loaded_data_retry(collection: MagicMock, console_print_mock: MagicMock, mock_collections):
    
    expected_response = {
        "ids": [],
        "embeddings":[],
        "documents":[],
        "uris":[""],
        "data":"",
        "metadatas":[""],
        "included":"documents"
    }
    
    mocked_response = GetResult(
        ids=[],
        embeddings=[],
        documents=[],
        uris=[""],
        data="",
        metadatas=[""],
        included="documents"
    )
    
    collection.get.return_value = mocked_response
    
    result = mock_collections.update_loaded_data(collection, "control", True)
    
    assert result == expected_response
    collection.get.assert_called()
    
    console_print_mock.assert_any_call(
        message=ANY,
        message_color=OutputColors.WARNING.value,
        app=Configuration.CHROMA_QUEUE
    )
    
    
@patch("chroma.app.domain.chroma_collections.Collection")
def test_basic_chroma_query(collection: MagicMock, mock_collections, mock_embedder_function):
    
    expected_response = {
        "ids": ["123"],
        "documents":["Some document"],
        "metadatas":["123"],
    }
    
    mocked_response = GetResult(
        ids=[["123"]],
        embeddings=[],
        documents=["Some document"],
        uris=[""],
        data="",
        metadatas=[["123"]],
        included="documents"
    )
    
    collection.query.return_value = mocked_response
    
    result = mock_collections.basic_chroma_query(collection, "control", "Some query")
    
    assert result == expected_response
    collection.query.assert_called()

@patch("chroma.app.domain.chroma_collections.Collection")
def test_basic_chroma_query(collection: MagicMock, mock_collections, mock_embedder_function):
    mocked_response = GetResult(
        ids=[["123"]],
        embeddings=[],
        documents=[],
        uris=[""],
        data="",
        metadatas=[["123"]],
        included="documents"
    )
    
    collection.query.return_value = mocked_response
    
    result = mock_collections.basic_chroma_query(collection, "control", "Some query")
    
    assert result == False
    collection.query.assert_called()
    

@patch("chroma.app.domain.chroma_collections.Collection")
def test_add_document_embeds(collection_mock: MagicMock, mock_collections, mock_embedder_function):
    collection_mock.add.return_value = None
    response = mock_collections.add_document_embeds(collection_mock, "Some document", {"sample": "sample"})
    assert response == True


def test_validate_loaded_response(mock_collections):
    loaded_data = {
        'data': {
            'ids': ['']
            }
        }
    expected_response = True, {'ids': ['']}, ""
    response = mock_collections._validate_loaded_response(
        loaded_data
    )
    assert response == expected_response


def test_validate_loaded_response_root_ids(mock_collections):
    loaded_data = {
            'ids': ['']
        }
    expected_response = True, {'ids': ['']}, ""
    response = mock_collections._validate_loaded_response(
        loaded_data
    )
    assert response == expected_response


def test_validate_loaded_response_no_data(mock_collections):
    expected_response = False, {}, "No information found at present for this category."
    response = mock_collections._validate_loaded_response({})
    assert response == expected_response


def test_validate_existing_collection(mock_collections, mock_embedder_function):
    mock_collections._chroma_client.get_collection.return_value = "some_collection"
    response = mock_collections._validate_existing_collection('some')
    
    assert "some_collection" == response
    
    
def test_validate_existing_collection_not_created(mock_collections, mock_embedder_function):
    # Mock EmbedderFunction to return a MagicMock
    with patch('chroma.app.domain.chroma_collections.ChromaCollections.EmbedderFunction',
               return_value=mock_embedder_function[0].return_value):
        # Set side effect to raise an InvalidCollectionException when get_collection is called
        with patch('chroma.app.domain.chroma_collections.chromadb.errors.InvalidCollectionException', Exception):
            mock_collections._chroma_client.get_collection.side_effect = InvalidCollectionException("Test exception")
            
            # Mock create_collection to return a mock collection
            mock_collections._chroma_client.create_collection.return_value = "some_collection"
            
            # Call the function
            response = mock_collections._validate_existing_collection('some')
            
            # Assert that the response is correct
            assert response == "some_collection"
            mock_collections._chroma_client.create_collection.assert_called_once_with(
                name='some',
                embedding_function=mock_embedder_function[0].return_value,
                metadata={"hnsw:space": "cosine"}
            )

@patch("chroma.app.domain.chroma_collections.loaded_collections", new={})
@patch("chroma.app.domain.chroma_collections.Collection")
def test_load_category_data(mock_collection, mock_collections):
    # Mock update_loaded_data to return a dict with data and expiration_time
    mock_collections.update_loaded_data = MagicMock()
    mock_collections.update_loaded_data.return_value = {
        'data': 'response',
        'expiration_time': time.time() + 600  # Set expiration to a future time
    }
    
    # Call load_category_data for the first time to trigger update_loaded_data
    response = mock_collections.load_category_data('control', mock_collection)
    
    # Verify that update_loaded_data was called once
    mock_collections.update_loaded_data.assert_called_once_with(mock_collection, 'control')

    # Check that the returned response matches the expected structure
    assert response == {
        'data': 'response',
        'expiration_time': mock_collections.update_loaded_data.return_value['expiration_time']
    }
    
@patch("chroma.app.domain.chroma_collections.loaded_collections",
       new={'control': {'expiration_time': time.time()}})
@patch("chroma.app.domain.chroma_collections.Collection")
def test_load_category_data_future_expiration(mock_collection, mock_collections):
    # Mock update_loaded_data to return a dict with data and expiration_time
    mock_collections.update_loaded_data = MagicMock()
    mock_collections.update_loaded_data.return_value = {
        'data': 'response',
        'expiration_time': time.time() + 100000  # Set expiration to a future time
    }
    
    # Call load_category_data for the first time to trigger update_loaded_data
    response = mock_collections.load_category_data('control', mock_collection)
    
    # Verify that update_loaded_data was called once
    mock_collections.update_loaded_data.assert_called_once_with(mock_collection, 'control')

    # Check that the returned response matches the expected structure
    assert response == {
        'data': 'response',
        'expiration_time': mock_collections.update_loaded_data.return_value['expiration_time']
    }
    

@patch('utils.outputs.print_console_message')
@patch("chroma.app.domain.chroma_collections.pdf_to_bytes")
def test_process_pdf_file(pdf_to_bytes_mock: MagicMock, console_print_mock, mock_collections, mock_embedder_function):
    mock_collections._validate_existing_collection = MagicMock()
    mock_collections._validate_existing_collection.return_value = MagicMock()
    
    mock_collections.add_document_embeds.return_value = "created_embed"
    pdf_to_bytes_mock.return_value = b'Some bytes'
    
    expected_response = {"STATE": "OK", "DESCRIPTION": "Successfully processed file"}
    response = mock_collections.process_pdf_file("/", ["control"], "collection")
    
    assert response == expected_response
    console_print_mock.assert_any_call(
        message=ANY,
        message_color=OutputColors.BOLD.value,
        app=Configuration.CHROMA_QUEUE
    )
    console_print_mock.assert_any_call(
        message=ANY,
        message_color=OutputColors.OKGREEN.value,
        app=Configuration.CHROMA_QUEUE
    )

@patch("chroma.app.domain.chroma_collections.ChromaCollections.update_loaded_data")
@patch("chroma.app.domain.chroma_collections.ChromaCollections.basic_chroma_query")
@patch("chroma.app.domain.chroma_collections.Collection")
@patch('utils.outputs.print_console_message')
def test_execute_search_query(console_print_mock: MagicMock,
                              collection_mock: MagicMock,
                              basic_chroma_query_mock: MagicMock,
                              update_loaded_data_mock: MagicMock,
                              mock_collections,
                              mock_embedder_function):
    
    expected_result = {'DESCRIPTION': 'Your search yielded no results.', 'STATE': 'ERROR'}
    
    # Mock collection.query to return expected keys
    collection_mock.query.return_value = {
        'documents': [['doc1', 'doc2']],
        'metadatas': [['meta1', 'meta2']],
        'ids': [['id1', 'id2']]
    }
    
    update_loaded_data_mock.return_value = None
    
    # Mock basic_chroma_query to use the mocked collection
    basic_chroma_query_mock.return_value = False
    
    # Mock _invoke_llm to return a response
    mock_collections._invoke_llm = MagicMock(return_value="llm response")
    
    # Mock _validate_existing_collection
    mock_collections._validate_existing_collection = MagicMock(return_value=collection_mock)
    
    # Mock load_category_data to return a non-empty dictionary
    mock_collections.load_category_data = MagicMock(return_value={'data': {}})
    
    # Mock _validate_loaded_response to return found data
    mock_collections._validate_loaded_response = MagicMock(return_value=(True, {}, ""))
    
    # Call execute_search_query
    response = mock_collections.execute_search_query(
        "collection",
        "control",
        "what is an action",
        12345,
        max_tries=5
    )
    
    # Assertions
    assert response == expected_result
    # Adjusted assertion for basic_chroma_query
    mock_collections._validate_existing_collection.assert_called_once_with("collection")
    mock_collections.load_category_data.assert_called_with(category='control', collection=collection_mock)
    mock_collections._validate_loaded_response.assert_called_with({'data': {}})
    basic_chroma_query_mock.assert_called_with(collection_mock, 'control', 'what is an action')
    update_loaded_data_mock.assert_called()
    
    # Ensure print_console_message is called correctly
    console_print_mock.assert_called_with(message='Your search yielded no results.',
                                          message_color=OutputColors.FAIL.value,
                                          app=Configuration.CHROMA_QUEUE)
    