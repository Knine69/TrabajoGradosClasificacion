
import chromadb
import torch
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

    class EmbedderFunction(EmbeddingFunction):
        def __init__(self) -> None:
            super().__init__()
            self.tokenizer = ChromaClient.tokenizer
            self.embedding_model = ChromaClient.embedding_model

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

    def basic_chroma_query(self,
                           collection: Collection,
                           document: list[Document]) -> None:
        results = collection.query(
            n_results=10,
            query_texts=document,
            where_document={"$contains": "input entered"}
            ).items()

        print(f"Results are: {results}")

    def add_document_embbeds(self, collection: Collection, document: Document):
        collection.add(
            documents=[document],
            metadatas=[{"category": "chemistry"}],
            # TODO: check how to validate last ID or create some new
            ids=["id1"]
        )

    def execute_basic_chroma_query(self):
        collection = (
            self._chroma_client.create_collection(
                name="my_collection",
                embedding_function=ChromaClient.EmbedderFunction()))

        pdf_text = pdf_to_bytes('test_file.pdf')
        sample_doc = pdf_text.decode('utf-8')

        self.add_document_embbeds(collection, sample_doc)

        # TODO: Load by category either at the start or lazily (preferred)
        loaded_db_data = (
            collection.get(where={"category": "chemistry"})['documents'])

        self.basic_chroma_query(collection, loaded_db_data)


if __name__ == "__main__":
    sample_client = ChromaClient()
    sample_client.execute_basic_chroma_query()
