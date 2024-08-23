
import chromadb
import torch
from chromadb.api.types import Document
from transformers import AutoTokenizer, AutoModel
from user_langchain.prompt import prompt
from langchain.agents import AgentExecutor, create_react_agent
from langchain_community.llms.ollama import Ollama
from chromadb import Documents, EmbeddingFunction, Embeddings
from chromadb.api.models.Collection import Collection
from tools.tools import tools
from pdfminer.high_level import extract_text


llm_model = Ollama(model="llama3")


tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
embedding_model = AutoModel.from_pretrained("bert-base-multilingual-cased")


class EmbedderFunction(EmbeddingFunction):
    def __init__(self) -> None:
        super().__init__()
        self.tokenizer = tokenizer
        self.embedding_model = embedding_model

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


def pdf_to_bytes(pdf_path):
    all_text = extract_text(pdf_path)

    text_bytes = all_text.encode('utf-8')

    return text_bytes


def basic_chroma_query(collection: Collection, document: Document) -> None:
    results = collection.query(
        n_results=10,
        query_texts=[document],
        where_document={"$contains": "input entered"}
        ).values()

    print(f"Results are: {results}")


def add_document_embbeds(collection: Collection, document: Document):
    collection.add(
        documents=[document],
        metadatas=[{"sample": "1", "page": "1"}],
        ids=["id1"]
    )


def invoke_query(executor, query, max_attempts=5):

    def output_handler(string):
        black_list = ["stopped", "limit", 'not a valid tool']
        output_response = any(word in string['output']
                              for word in black_list)

        if output_response:
            for step in string['intermediate_steps']:
                if isinstance(step[1], str):
                    if not any(word in step[1] for word in black_list):
                        return step[1]
                elif isinstance(step[1], int):
                    return step[1]

            raise ValueError("Couldn't process query")
        else:
            return string['output']

    for attempt in range(max_attempts):
        try:
            result = executor.invoke({"input": query})
            return {
                'query_made': query,
                'output': output_handler(result)
                }
        except Exception as e:
            print(f"Something failed: {e}")
        print(f"Attempt {attempt + 1}")
    return {"output": False, "description": "Too many failed attempts"}


def execute_agent_query():
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


def execute_basic_chroma_query():
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
    basic_chroma_query(collection, sample_doc)


if __name__ == "__main__":
    execute_agent_query()
    execute_basic_chroma_query()
