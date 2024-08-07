from transformers import AutoTokenizer, AutoModelForMaskedLM
from chromadb.api.types import Document
from chromadb.api.models.Collection import Collection
from chromadb import Documents, EmbeddingFunction, Embeddings

import torch
import chromadb
import fitz


llm_model = AutoModelForMaskedLM.from_pretrained("bert-base-multilingual-cased", output_hidden_states=True)


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
            
            print(f"Outputs are: {outputs}")
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


def basic_chroma_query(collection: Collection) -> None:
    results = collection.query(
        n_results=10,
        query_texts=sample_doc,
        where_document={"$contains": "input entered"}
        ).values()

    print(f"Results are: {results}")


def add_document_embbeds(collection: Collection, document: bytes):
    collection.add(
        documents=[sample_doc],
        metadatas=[{"sample": "1", "page": "1"}],
        ids=["id1"]
    )
    
# Initialize ChromaDB client and create a collection with the embedding function
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection", embedding_function=EmbedderFunction())

# Prepare text data in PDF file/s
pdf_text = pdf_to_bytes('test_file.pdf')
sample_doc = pdf_text.decode('utf-8')

# Add the document to the collection
add_document_embbeds(collection, sample_doc)

# Query the collection
basic_chroma_query(collection)
