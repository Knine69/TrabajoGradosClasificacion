from transformers import AutoTokenizer
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms.ollama import Ollama
from user_langchain.prompt import prompt
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Document
import chromadb
import torch
import fitz

from tools.tools import tools


llm_model = Ollama(model="llama2")


class EmbedderFunction(EmbeddingFunction):
    tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")

    def __init__(self) -> None:
        super().__init__()
        self.model = llm_model

    def __call__(self, input: Documents) -> Embeddings:
        embedding_results = []

        for doc in input:
            inputs = self.tokenizer(doc,
                                    return_tensors="pt",
                                    padding=True,
                                    truncation=True,
                                    max_length=512)

            with torch.no_grad():
                outputs = self.model(**inputs)

            hidden_states = outputs.hidden_states

            last_hidden_state = hidden_states[-1]

            embeddings = torch.mean(last_hidden_state, dim=1)

            # Aggregate embeddings by taking the mean
            embeddings = torch.mean(embeddings, dim=1)
            embedding_results.append(embeddings.numpy().tolist())

        return embedding_results


def pdf_to_bytes(pdf_path):
    document = fitz.open(pdf_path)
    all_text = ""

    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text = page.get_text()
        all_text += text

    text_bytes = all_text.encode('utf-8')

    return text_bytes


def basic_chroma_query(collection: Collection, document: bytes) -> None:
    results = collection.query(
        n_results=10,
        query_texts=[document],
        where_document={"$contains": "input entered"}
        ).values()

    print(f"Results are: {results}")


def add_document_embbeds(collection: Collection, document: bytes):
    collection.add(
        documents=[document],
        metadatas=[{"sample": "1", "page": "1"}],
        ids=["id1"]
    )


def invoke_query(executor, query, max_attempts=5):

    def black_listed_words(string):
        black_list = ["stopped", "limit"]
        output_response = any(word in string['output']
                              for word in black_list)
        # Validate if intermediate steps does not have black listed words
        # Then return first returned value

        if output_response:
            for step in string['intermediate_steps']:
                if isinstance(step[1], str):
                    if not any(word in step[1] for word in black_list):
                        return step[1]
                elif isinstance(step[1], int):
                    return step[1]
        else:
            return string['output']

    for attempt in range(max_attempts):
        try:
            result = executor.invoke({"input": query})
            return {
                'query_made': query,
                'output': black_listed_words(result)
                }
        except Exception as e:
            print(f"Something failed: {e}")
        print(f"Attempt {attempt + 1}")
    return {"output": False, "description": "Too many failed attempts"}


if __name__ == "__main__":
    agent = create_react_agent(llm_model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent,
                                   tools=tools,
                                   verbose=True,
                                   handle_parsing_errors=True,
                                   max_iterations=5,
                                #    callbacks=m,   TODO: Validate if behaviour can be corrected with callbacks
                                   return_intermediate_steps=True)

    query = "Cuál es la longitud de la palabra 'juan'"
    result = invoke_query(agent_executor, query)

    if result['output']:
        print(f"Query result is: {result}")
    else:
        print(f"Query failed: {result['description']}")

    # Initialize ChromaDB client and create a collection with the embedding
    # function
    chroma_client = chromadb.Client()
    collection = (
        chroma_client.create_collection(name="my_collection",
                                        embedding_function=EmbedderFunction()))

    # Prepare text data in PDF file/s
    pdf_text = pdf_to_bytes('test_file.pdf')
    sample_doc = pdf_text.decode('utf-8')

    # Add the document to the collection
    add_document_embbeds(collection, sample_doc)

    # Query the collection
    basic_chroma_query(collection)
