from typing import List
from bert_score import score
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer, util
from langchain_community.llms.ollama import Ollama
from langchain.chains.base import Chain
from user_langchain.llm_tests.test_prompt import prompt
import torch
import spacy


class LlmResponseValidator:
    def __init__(self):
        self.llm_model = Ollama(model="llama3:70b",
                                base_url="http://localhost:11434",
                                temperature=0.2,
                                top_p=40,
                                ).set_verbose(verbose=True)
        self.llm_chain: Chain = prompt | self.llm_model
        self.spacy_nlp = spacy.load("en_core_web_sm")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def calculate_bertscore(self, predictions: List[str], references: List[str], lang="en") -> dict:
        """Calculate BERTScore for the given predictions and references."""
        P, R, F1 = score(predictions, references, lang=lang)
        return {
            "precision": P.mean().item(),
            "recall": R.mean().item(),
            "f1": F1.mean().item()
        }

    def calculate_entity_coverage(self, prediction: str, reference: str) -> float:
        """Calculate the proportion of entities from the reference text that are covered in the prediction."""
        ref_doc = self.spacy_nlp(reference)
        pred_doc = self.spacy_nlp(prediction)
        
        ref_entities = {ent.text.lower() for ent in ref_doc.ents}
        pred_entities = {ent.text.lower() for ent in pred_doc.ents}
        
        if not ref_entities:
            return 1.0  # If there are no entities in the reference, consider coverage as 100%
        
        covered_entities = len(ref_entities & pred_entities)
        return covered_entities / len(ref_entities)

    def calculate_relevance(self, generated_answer: str, user_query: str) -> float:
        # Compute embeddings for both the generated answer and the user query
        embeddings1 = self.model.encode(generated_answer, convert_to_tensor=True)
        embeddings2 = self.model.encode(user_query, convert_to_tensor=True)
        
        # Compute the cosine similarity between the embeddings
        relevance_score = util.cos_sim(embeddings1, embeddings2).item()
        
        return relevance_score
    
    
    def calculate_completeness(self, generated_answer: str, expected_answer: str) -> float:
        # Split the expected answer into key concepts or keywords
        expected_keywords = set(expected_answer.lower().split())
        generated_keywords = set(generated_answer.lower().split())
        
        # Calculate the proportion of expected keywords found in the generated answer
        covered_keywords = len(expected_keywords & generated_keywords)
        
        return covered_keywords / len(expected_keywords) if expected_keywords else 0


    def execute_chain_query_with_metrics(self, documents, user_query, expected_answer):
        result = self.llm_chain.invoke({"question": user_query, "references": documents})
        
        # BERTScore
        bert_score = self.calculate_bertscore([result], [expected_answer])
        
        # Entity-Based Coverage
        entity_coverage = self.calculate_entity_coverage(result, expected_answer)
        
        # Relevance
        relevance = self.calculate_relevance(result, user_query)
        
        # Coverage
        coverage = self.calculate_completeness([result], documents)
        
        return {
            "response": result,
            "bertscore": bert_score,
            "entity_coverage": entity_coverage,
            "completeness": coverage,
            "relevance": relevance
        }
        

if __name__ =="main":
    response_validator = LlmResponseValidator()
    print(f"Llm Response Validation: \n{response_validator.execute_chain_query_with_metrics(
        documents=["a thing done; an act.", "something to be done"],  # RAG documents
        user_query="What is an action",  # Generate more
        expected_answer="An action is the fact or process of doing something, typically to achieve an aim."
        )}")