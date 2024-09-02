import chromadb
import torch

from transformers import AutoTokenizer, AutoModel
from chromadb import Documents, EmbeddingFunction, Embeddings

from chroma.category.types import FileCategories
from chroma.flask.domain.chroma_collections import ChromaCollections

from flask import Blueprint, request, jsonify

chroma_router = Blueprint('chroma', __name__, url_prefix='/chroma')


class ChromaClient:
    tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
    embedding_model = AutoModel.from_pretrained("bert-base-multilingual-cased")

    def __init__(self) -> None:
        # TODO: research db indexation
        self._chroma_client = chromadb.PersistentClient(path='./chroma')
        self._chroma_collections = ChromaCollections(self._chroma_client)

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
    def _validate_params(*args) -> bool:
        for arg in args:
            if not arg:
                return False
        return True

    @chroma_router.get("/documents")
    def execute_basic_chroma_query(self):
        collection_name = request.args.get('collection')
        category = request.args.get('category')
        search_text = request.args.get('search_text')

        if ChromaClient._validate_params(
                collection_name, category, search_text):
            return jsonify(self._chroma_collections.execute_search_query(
                collection_name, category, search_text
            ))

        return jsonify({
            'STATE': 'Query failed',
            'DESCRIPTION': 'Please provide enough information to '
            'execute the query.'})

    @chroma_router.post("/embed_document")
    def process_pdf_file(self):
        file_path = request.args.get('file_path')
        categories = request.args.getlist('categories')
        collection_name = request.args.get('collection_name')

        if ChromaClient._validate_params(
                file_path, categories, collection_name):
            return jsonify(self._chroma_collections.process_pdf_file(
                file_path, categories, collection_name
            ))

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
