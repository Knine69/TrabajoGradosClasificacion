import chromadb
import time

from chromadb.errors import InvalidDimensionException
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes

from chroma.flask import loaded_collections
from chroma.category.types import FileCategories
from chroma.flask.controller.chroma_client import ChromaClient

from utils.outputs import OutputColors, print_console_message


class ChromaCollections:
    def __init__(self, chroma_client: chromadb):
        self._chroma_client = chroma_client

    def validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(
                name=collection_name,
                embedding_function=ChromaClient.EmbedderFunction())
        except (ValueError, InvalidDimensionException):
            print_console_message(message_color=OutputColors.WARNING.value,
                                  message="Collection does not exist.")
            print_console_message(message_color=OutputColors.HEADER.value,
                                  message="Creating collection...")
            return (
                self._chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=ChromaClient.EmbedderFunction()))
        return result

    @staticmethod
    def create_metadata_object(categories_list: list[str]) -> dict:
        result = {}
        for category in categories_list:
            aux = category.lower()
            if FileCategories(aux):
                result[aux] = True

        return result

    @staticmethod
    def load_category_data(category: str, collection: Collection):
        if category in loaded_collections.keys():
            if time.time() < loaded_collections[category]['expiration_time']:
                return loaded_collections[category]

            return ChromaCollections.update_loaded_data(collection, category)
        else:
            return ChromaCollections.update_loaded_data(collection, category)

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
                           contained_text: str) -> dict:
        results = collection.query(
            n_results=10,
            query_texts=document,
            where_document={"$contains": contained_text}
        ).items()

        results = dict(results)

        return {"query_result": results} if bool(results['documents'][0]) else \
            {}

    @staticmethod
    def add_document_embbeds(collection: Collection,
                             document: str,
                             metadata_filter: [dict[str, str]],
                             ids: list[str]):
        try:
            collection.add(
                documents=[document],
                metadatas=metadata_filter,
                ids=ids
            )

            return True
        except ValueError as e:
            print_console_message(message=str(e),
                                  message_color=OutputColors.FAIL.value)
            return False

    def process_pdf_file(self, file_path, categories, collection_name):
        collection = self.validate_existing_collection(collection_name)

        pdf_text = pdf_to_bytes(file_path)
        sample_doc = pdf_text.decode('utf-8')

        result = self.add_document_embbeds(
            collection,
            sample_doc,
            [
                self.create_metadata_object(categories)
            ],
            [str(time.time())])

        if result:
            print_console_message(
                message_color=OutputColors.OKCYAN.value,
                message=f"Successfully processed: {file_path}")
            return {"STATE": "OK", "DESCRIPTION": "Successfully processed file"}

        return {"STATE": "ERROR", "DESCRIPTION": "Something went wrong"}

    def execute_search_query(self,
                             collection_name,
                             category,
                             search_text,
                             max_tries: int = 2):
        collection = self.validate_existing_collection(collection_name)

        loaded_db_data = ChromaCollections.load_category_data(
            category=category,
            collection=collection)

        counter = 0

        while (
                query_result := ChromaCollections.basic_chroma_query(
                collection,
                loaded_db_data['documents'],
                search_text)
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

        return {
            "STATE": "OK",
            "DESCRIPTION": "Successfully performed your query",
            "RESPONSE_DATA": query_result
        }
