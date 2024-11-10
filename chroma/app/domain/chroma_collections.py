import chromadb
import time
import torch
import requests
import json
import gc

from gensim.parsing import remove_stopwords
from transformers import AutoTokenizer, AutoModel
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from documents.utils import pdf_to_bytes

from chroma.app import loaded_collections
from chroma.category.types import FileCategories
from chroma_ms_config import Configuration
from utils.outputs import (print_warning_message,
                           print_successful_message,
                           print_header_message,
                           print_bold_message,
                           print_error)


def chunk_text(text: str, max_chunk_length=1024) -> tuple:
    """
    Chunk the text into smaller parts that fit within the model's max token
    limit.
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
        self._chroma_client = chromadb.HttpClient(host=Configuration.CHROMA_URL,
                                                  port=8000)
        
    class EmbedderFunction(EmbeddingFunction):
        def __init__(self):
            self.tokenizer = (
                AutoTokenizer.from_pretrained("bert-base-multilingual-cased"))
            self.embedding_model = (
                AutoModel.from_pretrained("bert-base-multilingual-cased"))

        def __call__(self, doc_input: Documents) -> Embeddings:
            embedding_results = []
            batch_size = 128
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

                # Convert embeddings to lists of floats
                for embedding in embeddings:
                    embedding_results.append(embedding.cpu().numpy().tolist())

            print_bold_message(f"Embeddings are: {embedding_results}", Configuration.CHROMA_QUEUE)
            
            # Check if embeddings are valid
            if not embedding_results or any(not isinstance(e, list) for e in embedding_results):
                print_error("Embeddings are invalid or empty.", app=Configuration.CHROMA_QUEUE)
            return embedding_results


    @staticmethod
    def create_metadata_object(categories_list: list[str]) -> dict:
        result = {}
        for category in categories_list:
            aux = category.lower()
            if FileCategories(aux):
                result[aux] = 1

        return result

    @staticmethod
    def update_loaded_data(collection: Collection,
                        category: str,
                        re_query: bool = False) -> dict:
        if re_query:
            print_warning_message("Nothing found, updating loaded data...", Configuration.CHROMA_QUEUE)
        else:
            print_warning_message("Updating loaded data...", Configuration.CHROMA_QUEUE)

        # Include embeddings in the get method
        aux = dict(collection.get(where={category: 1}, include=["embeddings", "metadatas", "documents"]).items())
        
        print_successful_message(f"Loaded data: {aux}", Configuration.CHROMA_QUEUE)
        
        response_dict = {
            'data': aux,
            'expiration_time': time.time() + (60 * 10)
        }

        loaded_collections[category] = response_dict
        return response_dict['data']

    @staticmethod
    def basic_chroma_query(collection: Collection,
                        category: str,
                        user_query: str,
                        max_results: int = 5) -> dict:

        query_no_stopwords = remove_stopwords(user_query)
        query_terms = query_no_stopwords.split()

        query_embeddings = [
            ChromaCollections.EmbedderFunction()([term])[0]
            for term in query_terms
        ]

        document_scores = {}
        metadata_scores = {}
        id_scores = {}

        for query_embedding in query_embeddings:
            try:
                where_clause = {f"{category}": 1} if category else None

                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_results,
                    where=where_clause,
                    include=["embeddings", "metadatas", "documents", "distances"]
                )
            except Exception as e:
                print_error(f"Error querying ChromaDB: {str(e.with_traceback(e.__traceback__))}", app=Configuration.CHROMA_QUEUE)
                results = {"documents": [], "metadatas": [], "ids": []}

            for i, doc in enumerate(results['documents']):
                doc_id = results['ids'][0][i]
                metadata = results['metadatas'][0][i]

                if doc_id in document_scores:
                    document_scores[doc_id].append(doc)
                    metadata_scores[doc_id].append(metadata)
                else:
                    document_scores[doc_id] = [doc]
                    metadata_scores[doc_id] = [metadata]
                    id_scores[doc_id] = doc_id

        sorted_docs = sorted(
            document_scores.keys(),
            key=lambda dcmnt_id: len(document_scores[dcmnt_id]), reverse=True)

        top_results = {
            'documents': [
                document_scores[doc_id][0]
                for doc_id in sorted_docs[:max_results]],
            'metadatas': [
                metadata_scores[doc_id][0]
                for doc_id in sorted_docs[:max_results]],
            'ids': [id_scores[doc_id] for doc_id in sorted_docs[:max_results]],
        }
        
        gc.collect()

        return top_results if top_results['documents'] else False


    @staticmethod
    def add_document_embeds(collection: Collection,
                            document: str,
                            metadata_filter: dict[str, str]):
        try:
            document_chunks, ids = chunk_text(document)
            embeddings = ChromaCollections.EmbedderFunction()(document_chunks)
            collection.add(
                documents=document_chunks,
                metadatas=[metadata_filter] * len(document_chunks),
                embeddings=embeddings,
                ids=ids
            )
            print_bold_message(f"Stored embeddings are: {embeddings}", Configuration.CHROMA_QUEUE)
            gc.collect()
            return True
        except Exception as e:
            print_error(message=str(e), app=Configuration.CHROMA_QUEUE)
            return False

    @staticmethod
    def _invoke_llm(query_result, user_query, task_id):
        try:
            response = requests.post(
                url="http://localhost:5001/langchain/search",
                json={
                    "categories": query_result.get("metadatas", []),
                    "documents": query_result.get("documents", []),
                    "user_query": user_query,
                    "task_id": task_id
                },
                headers={
                    "Content-Type": "application/json"
                }
            )
            response_content = response.content.decode('utf-8').strip()
            response_content = response_content.replace('data:', '').strip()
            response_data = json.loads(response_content)

            if response_data["STATE"] == "ERROR":
                print_error(response_data["DESCRIPTION"],
                            Configuration.LANGCHAIN_QUEUE)
            else:
                print_successful_message(response_data["DESCRIPTION"],
                                         Configuration.LANGCHAIN_QUEUE)
                gc.collect()
            return {
                "STATE": "SUCCESS",
                "RESPONSE_DATA": response_data
            }
        except requests.exceptions.ConnectionError as e:
            print_error(f"Something went wrong: {str(e)}",
                        Configuration.CHROMA_QUEUE)
            return {
                "STATE": "ERROR",
                "DESCRIPTION": str(e)
            }
        except requests.exceptions.JSONDecodeError as e:
            print_error(f"Failed to decode JSON: {e}",
                        Configuration.CHROMA_QUEUE)
            return {
                "STATE": "ERROR",
                "DESCRIPTION": "Could not process response JSON"
            }

    @staticmethod
    def _validate_loaded_response(loaded_db_data: dict) -> tuple:
        if loaded_db_data.get('data', None):
            if loaded_db_data['data'].get('ids', None):
                return True, loaded_db_data['data'], ""
        else:
            if loaded_db_data.get('ids', None):
                return True, loaded_db_data, ""

        return (False,
                loaded_db_data,
                "No information found at present for this category.")

    @staticmethod
    def _parse_request(option: str, *data):
        return json.dumps(
            {
                'operation': option,
                'collection': data[0],
                'category': data[1],
                'user_query': data[2]
             }
        ) if option == "query" else json.dumps(
            {
                'operation': option,
                'collection': data[0],
                'file_path': data[1],
                'categories': data[2]}
        )

    def _validate_existing_collection(self, collection_name: str) -> Collection:
        try:
            result = self._chroma_client.get_collection(
                name=collection_name,
                embedding_function=ChromaCollections.EmbedderFunction())
        except (ValueError, chromadb.errors.InvalidCollectionException, Exception):
            print_warning_message(message="Collection does not exist.",
                                  app=Configuration.CHROMA_QUEUE)
            print_header_message(message="Creating collection...",
                                 app=Configuration.CHROMA_QUEUE)
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
        request_register = self._parse_request("embed",
                                               collection_name,
                                               file_path,
                                               categories)
        print_header_message(message=f"Received request: {request_register}",
                             app=Configuration.CHROMA_QUEUE)
        
        collection = self._validate_existing_collection(collection_name)

        pdf_text = pdf_to_bytes(file_path)
        sample_doc = pdf_text.decode('utf-8')

        start_time = time.time()
        result = self.add_document_embeds(
            collection,
            sample_doc,
            self.create_metadata_object(categories))

        end_time = time.time()

        if result:
            print_successful_message(
                f"Successfully processed: {file_path}",
                Configuration.CHROMA_QUEUE)
            print_bold_message(
                f"Document took {end_time - start_time}s to embedded",
                Configuration.CHROMA_QUEUE)

            return {"STATE": "OK", "DESCRIPTION": "Successfully processed file"}

        return {"STATE": "ERROR", "DESCRIPTION": "Something went wrong"}

    def execute_search_query(self,
                             collection_name,
                             category,
                             user_query,
                             task_id: int,
                             max_tries: int = 2):
        request_register = self._parse_request("query",
                                               collection_name,
                                               category,
                                               user_query)
        print_header_message(message=f"Received request: {request_register}",
                             app=Configuration.CHROMA_QUEUE)

        collection = self._validate_existing_collection(collection_name)

        
        loaded_db_data: dict = self.load_category_data(
            category=category,
            collection=collection)
        
        (found_data,
         loaded_db_data,
         response_message) = self._validate_loaded_response(loaded_db_data)
        if not found_data:
            print_error(response_message, Configuration.CHROMA_QUEUE)
            return {
                "STATE": "ERROR",
                "DESCRIPTION": response_message
            }

        counter = 0
        while (
                query_result := ChromaCollections.basic_chroma_query(
                    collection,
                    category,
                    user_query)
        ) is False:
            if counter == max_tries:
                err_message = "Your search yielded no results."
                print_error(err_message, Configuration.CHROMA_QUEUE)
                return {
                    "STATE": "ERROR",
                    "DESCRIPTION": err_message
                }

            ChromaCollections.update_loaded_data(
                collection=collection,
                category=category,
                re_query=True)

            print_warning_message("Retrying query...",
                                  Configuration.CHROMA_QUEUE)
            counter += 1
        print_successful_message(
            f"Successfully retrieved db data: {query_result}",
            Configuration.CHROMA_QUEUE)

        return self._invoke_llm(query_result, user_query, task_id)
