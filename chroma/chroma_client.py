import chromadb
import torch
import time
from transformers import AutoTokenizer, AutoModel
from chromadb.api.types import Document
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes


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

        print(f"Results are: {results}")

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

    def execute_basic_chroma_query(self, collection_name):
        collection = (
            self._chroma_client.create_collection(
                name=collection_name,
                embedding_function=ChromaClient.EmbedderFunction()))

        pdf_text = pdf_to_bytes('test_file.pdf')
        sample_doc = pdf_text.decode('utf-8')

        self.add_document_embbeds(
            collection,
            sample_doc,
            [
                {"category": "chemistry", "category2": "control"}
             ],
            [str(time.time())])

        # TODO: Load by category either at the start or lazily (preferred)
        loaded_db_data = (
            collection.get(where={"category": "chemistry"})['documents'])

        self.basic_chroma_query(collection, loaded_db_data, "input")


if __name__ == "__main__":
    sample_client = ChromaClient()
    sample_client.execute_basic_chroma_query("some_collection")
