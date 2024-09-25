import chromadb
import time
import torch
import requests
import json

from transformers import AutoTokenizer, AutoModel
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.errors import InvalidDimensionException
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes

from chroma.app import loaded_collections
from chroma.category.types import FileCategories

from utils.outputs import OutputColors, print_console_message


def chunk_text(text: str, max_chunk_length=1024) -> tuple:
    """
    Chunk the text into smaller parts that fit within the model's max token limit.
    """
    words = text.split()
    chunks = []
    ids = []
    for i in range(0, len(words), max_chunk_length):
        chunk = " ".join(words[i:i + max_chunk_length])
        chunks.append(chunk)
        ids.append(str(time.time()))
    return chunks, ids


class ChromaCollections:
    def __init__(self):
        self._chroma_client = chromadb.HttpClient(host='localhost', port=8000)

    class EmbedderFunction(EmbeddingFunction):

        tokenizer = (
            AutoTokenizer.from_pretrained("bert-base-multilingual-cased"))
        embedding_model = (
            AutoModel.from_pretrained("bert-base-multilingual-cased"))

        def __call__(self, doc_input: Documents) -> Embeddings:
            embedding_results = []
            batch_size = 16
            for i in range(0, len(doc_input), batch_size):
                batch_docs = doc_input[i:i + batch_size]
                inputs = self.tokenizer(batch_docs,
                                        return_tensors="pt",
                                        padding=True,
                                        truncation=True,
                                        max_length=512)

                with torch.no_grad():
                    outputs = self.embedding_model(**inputs)

                last_hidden_state = outputs.last_hidden_state
                embeddings = torch.mean(last_hidden_state, dim=1).squeeze()

                if len(embeddings.shape) == 1:
                    embeddings = [embeddings]

                for embedding in embeddings:
                    embedding_results.append(embedding.numpy().tolist())

            return embedding_results

    @staticmethod
    def create_metadata_object(categories_list: list[str]) -> dict:
        result = {}
        for category in categories_list:
            aux = category.lower()
            if FileCategories(aux):
                result[aux] = True

        return result

    @staticmethod
    def update_loaded_data(collection: Collection,
                           category: str,
                           re_query: bool = False) -> dict:
        if re_query:
            print_console_message(
                message="Nothing found, updating loaded data...",
                message_color=OutputColors.WARNING.value)
        else:
            print_console_message(
                message="Updating loaded data...",
                message_color=OutputColors.WARNING.value)
        aux = collection.get(where={category: True}).items()
        response_dict = {
            'data': dict(aux),
            'expiration_time': time.time() + (60 * 10)
        }

        loaded_collections[category] = response_dict
        return response_dict['data']

    @staticmethod
    def basic_chroma_query(collection: Collection,
                           document: list[str],
                           user_query: str,
                           max_results: int = 5) -> dict:

        query_embedding = ChromaCollections.EmbedderFunction()([user_query])[0]
        results = collection.query(
            n_results=max_results,
            # query_texts=document,
            query_embeddings=query_embedding,
            where_document={"$contains": user_query}
        ).items()

        results = dict(results)

        return results if bool(results['documents'][0]) else False

    @staticmethod
    def add_document_embeds(collection: Collection,
                            document: str,
                            metadata_filter: dict[str, str]):
        try:
            document_chunks, ids = chunk_text(document)
            collection.add(
                documents=document_chunks,
                metadatas=[metadata_filter] * len(document_chunks),
                embeddings=(
                    ChromaCollections.EmbedderFunction()(document_chunks)),
                ids=ids
            )

            return True
        except Exception as e:
            print_console_message(message=str(e),
                                  message_color=OutputColors.FAIL.value)
            return False

    def validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(
                name=collection_name,
                embedding_function=ChromaCollections.EmbedderFunction())
        except (ValueError, InvalidDimensionException, Exception):
            print_console_message(message_color=OutputColors.WARNING.value,
                                  message="Collection does not exist.")
            print_console_message(message_color=OutputColors.HEADER.value,
                                  message="Creating collection...")
            return (
                self._chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=ChromaCollections.EmbedderFunction(),
                    metadata={"hnsw:space": "cosine"}
                ))
        return result

    def load_category_data(self, category: str, collection: Collection):
        if category in loaded_collections.keys():
            if time.time() < loaded_collections[category]['expiration_time']:
                return loaded_collections[category]

            return self.update_loaded_data(collection, category)
        else:
            return self.update_loaded_data(collection, category)

    def process_pdf_file(self, file_path, categories, collection_name):
        collection = self.validate_existing_collection(collection_name)

        pdf_text = pdf_to_bytes(file_path)
        sample_doc = pdf_text.decode('utf-8')

        result = self.add_document_embeds(
            collection,
            sample_doc,
            self.create_metadata_object(categories))

        if result:
            print_console_message(
                message_color=OutputColors.OKCYAN.value,
                message=f"Successfully processed: {file_path}")
            return {"STATE": "OK", "DESCRIPTION": "Successfully processed file"}

        return {"STATE": "ERROR", "DESCRIPTION": "Something went wrong"}

    def execute_search_query(self,
                             collection_name,
                             category,
                             user_query,
                             max_tries: int = 2):
        collection = self.validate_existing_collection(collection_name)

        loaded_db_data: dict = self.load_category_data(
            category=category,
            collection=collection)

        print(f"Response data is: {loaded_db_data}")

        loaded_db_data = (
            loaded_db_data if loaded_db_data.get('documents', None)
            else loaded_db_data['data'])

        counter = 0

        while (
                query_result := ChromaCollections.basic_chroma_query(
                    collection,
                    loaded_db_data['documents'],
                    user_query)
        ) is False:
            if counter == max_tries:
                return {
                    "STATE": "ERROR",
                    "DESCRIPTION": "Your search yielded no results."
                }

            loaded_db_data = ChromaCollections.update_loaded_data(
                collection=collection,
                category=category,
                re_query=True)
            print_console_message(
                message="Retrying query...",
                message_color=OutputColors.WARNING.value)
            counter += 1

        print(f"Query result: {query_result}")

        response = requests.post(
            url="http://localhost:5001/langchain/search",
            json={
                "categories": query_result.get("metadatas", []),
                "documents": query_result.get("documents", []),
                "user_query": user_query
            },
            headers={
                "Content-Type": "application/json"
            }
        )

        print(f"Response is: {str(response)} - {response.content}")

        try:
            response_content = response.content.decode('utf-8').strip()
            response_content = response_content.replace('data:', '').strip()
            response_data = json.loads(response_content)

            return {
                "RESPONSE_DATA": response_data
            }

        except requests.exceptions.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
            return {
                "STATE": "ERROR",
                "DESCRIPTION": "Could not process response JSON"
            }

