from typing import List
from bert_score import score
from test_data import test_data
from sentence_transformers import SentenceTransformer, util
from langchain_community.llms.ollama import Ollama
from langchain.chains.base import Chain
from user_langchain.prompt import prompt, parser
import json
import spacy


class LlmResponseValidator:
    def __init__(self):
        self.llm_model = Ollama(model="llama3:70b",
                                base_url="http://192.168.0.71:11434",
                                temperature=0.2,
                                top_p=40,
                                )
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
        result = self.llm_chain.invoke({"question": user_query, "references": documents, 
                                          "format_instructions": parser})
       
        # BERTScore
        bert_score = self.calculate_bertscore([result], [expected_answer])
        
        # Entity-Based Coverage
        entity_coverage = self.calculate_entity_coverage(result, expected_answer)
        
        # Relevance
        relevance = self.calculate_relevance(result, user_query)
        
        # Coverage
        coverage = self.calculate_completeness(result, expected_answer)
        
        return {
            "response": result,
            "bertscore": bert_score,
            "entity_coverage": entity_coverage,
            "completeness": coverage,
            "relevance": relevance
        }


def accumulate_metrics(current, response) -> None:
    current["bertscore"]["precision"] += response["bertscore"]["precision"]
    current["bertscore"]["recall"] += response["bertscore"]["recall"]
    current["bertscore"]["f1"] += response["bertscore"]["f1"]
    current["entity_coverage"] += response["entity_coverage"]
    current["completeness"] += response["completeness"]
    current["relevance"] += response["relevance"]


def accumulate_aggregates(current, response):
    current["bertscore_precision"] += response["avg_bert_precision"]
    current["bertscore_recall"] += response["avg_bert_recall"]
    current["bertscore_f1"] += response["avg_bert_f1"]
    current["entity_coverage"] += response["avg_entity_coverage"]
    current["completeness"] += response["avg_completeness"]
    current["relevance"] += response["avg_relevance"]


def calculate_average_per_question():
    attempts_average_response = [
    ]
    
    for query, references, expected_answer in zip(
        test_data["user_queries"],
        test_data["documents"],
        test_data["expected_answers"]):
        
        accumulated_average_entry = {
            "bertscore": {
                "precision": 0.0,
                "recall": 0.0,
                "f1": 0.0
            },
            "entity_coverage": 0.0,
            "completeness": 0.0,
            "relevance": 0.0,
        }
        
        for _ in range(5):
            
            response = response_validator.execute_chain_query_with_metrics(
                documents=references,
                user_query=query,
                expected_answer=expected_answer
                )
            
            accumulate_metrics(accumulated_average_entry, response)
        
        attempts_average_response.append(
            {
                "question": query,
                "avg_bert_precision": accumulated_average_entry["bertscore"]["precision"] / 5,
                "avg_bert_recall": accumulated_average_entry["bertscore"]["recall"] / 5,
                "avg_bert_f1": accumulated_average_entry["bertscore"]["f1"] / 5,
                "avg_entity_coverage": accumulated_average_entry["entity_coverage"] / 5,
                "avg_completeness": accumulated_average_entry["completeness"] / 5,
                "avg_relevance": accumulated_average_entry["relevance"] / 5,
            }
        )
        
    return attempts_average_response


def calculate_aggregate_results(attempts_average_response: list):
    array_size = len(attempts_average_response)
    aggregate_results = {
        "bertscore_precision": 0.0,
        "bertscore_recall": 0.0,
        "bertscore_f1": 0.0,
        "entity_coverage": 0.0,
        "completeness": 0.0,
        "relevance": 0.0,
    }
    
    final_aggregated_results = {
        'entries_registered': attempts_average_response
    }
    
    for obj in attempts_average_response:
        accumulate_aggregates(aggregate_results, obj)
    
    final_aggregated_results["aggregate_results"] = {
        "bertscore_precision": aggregate_results["bertscore_precision"] / array_size,
        "bertscore_recall": aggregate_results["bertscore_recall"] / array_size,
        "bertscore_f1": aggregate_results["bertscore_f1"] / array_size,
        "entity_coverage": aggregate_results["entity_coverage"] / array_size,
        "completeness": aggregate_results["completeness"] / array_size,
        "relevance": aggregate_results["relevance"] / array_size
    }
    
    return final_aggregated_results


if __name__ =="__main__":
    print("Initiating response validation")
    response_validator = LlmResponseValidator()
    
    attempts_average_response = calculate_average_per_question()
    
    final_aggregated_results = calculate_aggregate_results(
        attempts_average_response=attempts_average_response)
    
    print(f"Llm Response Validation: \n{json.dumps(final_aggregated_results, indent=2)}")