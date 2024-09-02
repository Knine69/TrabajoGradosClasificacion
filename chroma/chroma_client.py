import chromadb
import torch
import time

from chromadb.errors import InvalidDimensionException
from transformers import AutoTokenizer, AutoModel
from chromadb.api.types import Document
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes
from utils.outputs import OutputColors
from chroma.category.types import FileCategories
from chroma import loaded_collections


class ChromaClient:
    tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
    embedding_model = AutoModel.from_pretrained("bert-base-multilingual-cased")

    def __init__(self) -> None:
        self._chroma_client = chromadb.PersistentClient(path='./chroma')

    class EmbedderFunction(EmbeddingFunction):
        def __init__(self) -> None:
            super().__init__()
            self.embedding_model = ChromaClient.embedding_model
            self.tokenizer = ChromaClient.tokenizer

        def __call__(self, doc_input: Documents) -> Embeddings:
            embedding_results = []

            for doc in doc_input:
                inputs = self.tokenizer(doc,
                                        return_tensors="pt",
                                        padding=True,
                                        truncation=True,
                                        max_length=512)

                with torch.no_grad():
                    outputs = self.embedding_model(**inputs)

                last_hidden_state = outputs.last_hidden_state
                embeddings = torch.mean(last_hidden_state, dim=1).squeeze()

                if embeddings.shape[-1] != 768:
                    raise ValueError("Embedding dimensionality mismatch.")

                embedding_results.append(embeddings.numpy().tolist())

            return embedding_results

    @staticmethod
    def basic_chroma_query(collection: Collection,
                           document: list[Document],
                           contained_text: str) -> dict:
        results = collection.query(
            n_results=10,
            query_texts=document,
            where_document={"$contains": contained_text}
            ).items()

        results = dict(results)

        ChromaClient.print_console_message(
            message_color=OutputColors.OKGREEN.value,
            message=f"Results are: {results}")

        return {"query_result": results} if bool(results['documents'][0]) else \
            {}

    @staticmethod
    def add_document_embbeds(collection: Collection,
                             document: Document,
                             metadata_filter: [dict[str, str]],
                             ids: list[str]):
        collection.add(
            documents=[document],
            metadatas=metadata_filter,
            ids=ids
        )

    @staticmethod
    def _create_metadata_object(categories_list: list[str]) -> dict:
        result = {}
        for category in categories_list:
            aux = category.lower()
            if FileCategories(aux):
                result[aux] = True

        return result

    @staticmethod
    def print_console_message(
            message: str,
            message_color: str = OutputColors.WHITE.value) -> None:
        print(f"{message_color}{message}{OutputColors.WHITE.value}")

    def _validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(
                name=collection_name,
                embedding_function=ChromaClient.EmbedderFunction())
        except (ValueError, InvalidDimensionException):
            self.print_console_message(message_color=OutputColors.WARNING.value,
                                       message="Collection does not exist.")
            self.print_console_message(message_color=OutputColors.HEADER.value,
                                       message="Creating collection...")
            return (
                self._chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=ChromaClient.EmbedderFunction()))
        return result

    @staticmethod
    def _load_category_data(category: str, collection: Collection):
        if category in loaded_collections.keys():
            if time.time() < loaded_collections[category]['expiration_time']:
                return loaded_collections[category]

            return ChromaClient.update_loaded_data(collection, category)
        else:
            return ChromaClient.update_loaded_data(collection, category)

    @staticmethod
    def update_loaded_data(collection: Collection,
                           category: str,
                           re_query: bool = False) -> dict:
        if re_query:
            ChromaClient.print_console_message(
                message="Nothing found, updating loaded data...",
                message_color=OutputColors.WARNING.value)
        else:
            ChromaClient.print_console_message(
                message="Updating loaded data...",
                message_color=OutputColors.WARNING.value)
        aux = collection.get(where={category: True}).items()
        response_dict = {
            'data': dict(aux),
            'expiration_time': time.time() + (60 * 10)
        }

        loaded_collections[category] = response_dict
        return response_dict['data']

    def execute_basic_chroma_query(self,
                                   collection_name: str,
                                   categories: list[str],
                                   search_text: str):
        collection = self._validate_existing_collection(collection_name)

        loaded_db_data = self._load_category_data(
            category=categories[0],
            collection=collection)

        query_result = self.basic_chroma_query(collection,
                                               loaded_db_data['documents'],
                                               search_text)
        if bool(query_result):
            return query_result

        loaded_db_data = ChromaClient.update_loaded_data(collection=collection,
                                                         category=categories[0],
                                                         re_query=True)
        ChromaClient.print_console_message(
            message="Retrying query...",
            message_color=OutputColors.WARNING.value)

        return self.basic_chroma_query(collection,
                                       loaded_db_data['documents'],
                                       search_text)

    def process_pdf_file(self,
                         file_path: str,
                         categories: list[str],
                         collection_name: str = None,
                         collection: Collection = None
                         ):
        collection = (collection if collection else
                      self._validate_existing_collection(collection_name))

        pdf_text = pdf_to_bytes(file_path)
        sample_doc = pdf_text.decode('utf-8')

        self.add_document_embbeds(
            collection,
            sample_doc,
            [
                self._create_metadata_object(categories)
            ],
            [str(time.time())])

        self.print_console_message(
            message_color=OutputColors.OKCYAN.value,
            message=f"Successfully processed: {file_path}")

    # TODO: access pdf directory Try bind mounts

    # TODO: Load pdf files from database into local file system


if __name__ == "__main__":
    sample_client = ChromaClient()
    sample_client.execute_basic_chroma_query("some_collection",
                                             [
                                                 FileCategories.CHEMISTRY.value,
                                                 FileCategories.CONTROL.value,
                                                 FileCategories.ROBOTICS.value,
                                             ],
                                             "hydrogenation")
