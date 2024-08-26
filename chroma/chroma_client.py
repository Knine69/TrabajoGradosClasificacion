import chromadb
import torch
import time
from transformers import AutoTokenizer, AutoModel
from chromadb.api.types import Document
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes
from utils.outputs import OutputColors


class ChromaClient:
    tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
    embedding_model = AutoModel.from_pretrained("bert-base-multilingual-cased")

    def __init__(self) -> None:
        self._chroma_client = chromadb.Client()
        self._loaded_collections = {}

    class EmbedderFunction(EmbeddingFunction):
        def __init__(self) -> None:
            super().__init__()
            self.embedding_model = ChromaClient.embedding_model
            self.tokenizer = ChromaClient.tokenizer

        def __call__(self, input: Documents) -> Embeddings:
            embedding_results = []

            for doc in input:
                inputs = self.tokenizer(doc,
                                        return_tensors="pt",
                                        padding=True,
                                        truncation=True,
                                        max_length=512)

                with torch.no_grad():
                    outputs = self.embedding_model(**inputs)

                last_hidden_state = outputs.last_hidden_state
                embeddings = torch.mean(last_hidden_state, dim=1).squeeze()

                embedding_results.append(embeddings.numpy().tolist())

            return embedding_results

    @staticmethod
    def basic_chroma_query(collection: Collection,
                           document: list[Document],
                           contained_text: str) -> None:
        results = collection.query(
            n_results=10,
            query_texts=document,
            where_document={"$contains": contained_text}
            ).items()

        ChromaClient.print_console_message(OutputColors.OKGREEN.value,
                                           f"Results are: {results}")

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
        count = 1
        for category in categories_list:
            result[f'category_{count}'] = category
            count += 1

        return result

    @staticmethod
    def print_console_message(message_color: str, message: str) -> None:
        print(f"{message_color}{message}{OutputColors.WHITE.value}")

    def _validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(name=collection_name)
        except ValueError:
            self.print_console_message(OutputColors.WARNING.value,
                                       "Collection does not exist.")
            self.print_console_message(OutputColors.HEADER.value,
                                       "Creating collection...")
            return (
                self._chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=ChromaClient.EmbedderFunction()))
        return result

    def execute_basic_chroma_query(self, collection_name):
        collection = self._validate_existing_collection(collection_name)

        self.process_pdf_file('test_file.pdf',
                              collection=collection,
                              categories=["chemistry"])

        # TODO: Load by category either at the start or lazily (preferred)
        loaded_db_data = (
            collection.get(where={"category_1": "chemistry"})['documents'])

        self.print_console_message(OutputColors.BOLD.value,
                                   f"Loaded data...\n{loaded_db_data}")

        self.basic_chroma_query(collection, loaded_db_data, "input")

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


if __name__ == "__main__":
    sample_client = ChromaClient()
    sample_client.execute_basic_chroma_query("some_collection")
