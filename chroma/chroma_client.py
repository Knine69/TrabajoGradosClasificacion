import chromadb
import torch
import time
from transformers import AutoTokenizer, AutoModel
from chromadb.api.types import Document
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes
from utils.outputs import OutputColors
from chroma.category.types import FileCategories


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

        ChromaClient.print_console_message(
            message_color=OutputColors.OKGREEN.value,
            message=f"Results are: {results}")

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
    def print_console_message(message: str,
                              message_color: str = OutputColors.WHITE.value) -> None:
        print(f"{message_color}{message}{OutputColors.WHITE.value}")

    def _validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(name=collection_name)
        except ValueError:
            self.print_console_message(message_color=OutputColors.WARNING.value,
                                       message="Collection does not exist.")
            self.print_console_message(message_color=OutputColors.HEADER.value,
                                       message="Creating collection...")
            return (
                self._chroma_client.create_collection(
                    name=collection_name,
                    embedding_function=ChromaClient.EmbedderFunction()))
        return result

    def _load_category_data(self, category: str, collection: Collection):
        if category in self._loaded_collections.keys():
            return self._loaded_collections[category]
        else:
            loaded_data = collection.get(where={category: True}).values()
            self._loaded_collections[category] = loaded_data

            return list(loaded_data)

    def execute_basic_chroma_query(self,
                                   collection_name: str,
                                   categories: list[str]):
        collection = self._validate_existing_collection(collection_name)

        self.process_pdf_file('test_file.pdf',
                              collection=collection,
                              categories=categories)
        self.process_pdf_file('chemistry_sample.pdf',
                              collection=collection,
                              categories=[categories[0]])

        loaded_db_data = self._load_category_data(
            category=categories[0],
            collection=collection)

        # TODO: if query empty, reload, update loaded dict and retry query,
        #  research indexing by category to reduce possible downtime

        self.basic_chroma_query(collection,
                                loaded_db_data[3],
                                "hydrogenation")

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


if __name__ == "__main__":
    sample_client = ChromaClient()
    sample_client.execute_basic_chroma_query("some_collection",
                                             [
                                                 FileCategories.CHEMISTRY.value,
                                                 FileCategories.CONTROL.value,
                                                 FileCategories.ROBOTICS.value,
                                             ])
