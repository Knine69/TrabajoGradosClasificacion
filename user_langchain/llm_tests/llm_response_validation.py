import math
from sklearn.metrics import average_precision_score
from bert_score import score  # Requires 'pip install bert-score'
from langchain.chains.base import Chain
from utils.outputs import print_error
from langchain_ms_config import Configuration
from langchain_community.llms import Ollama  # Import the Ollama model wrapper
from user_langchain.llm_tests.test_prompt import prompt
from typing import List


class LlmResponseValidator:
    def __init__(self, llm_model=None):
        # Initialize the Ollama model and Chain
        self.llm_model = llm_model or Ollama(model="llama3:70b", base_url="http://localhost:11434")
        self.llm_chain: Chain = prompt | self.llm_model

    def calculate_accuracy(self, results: List[str], expected_outputs: List[str]) -> float:
        """Calculate accuracy by checking if the generated answer matches expected answer."""
        correct_count = sum(1 for result, expected in zip(results, expected_outputs) if result == expected)
        return correct_count / len(expected_outputs) if expected_outputs else 0
    
    def calculate_mean_average_precision(self, y_true: List[int], y_pred: List[int]) -> float:
        """Calculate mean average precision between true and predicted relevance scores."""
        return average_precision_score(y_true, y_pred)

    def calculate_bertscore(self, predictions: List[str], references: List[str], lang="en"):
        """Calculate BERTScore between predictions and references."""
        P, R, F1 = score(predictions, references, lang=lang)
        return {"precision": P.mean().item(), "recall": R.mean().item(), "f1": F1.mean().item()}

    def calculate_approximate_perplexity(self, texts: List[str]) -> float:
        """
        Calculate an approximate perplexity based on response length and rough confidence.
        This is an approximation and does not represent true perplexity.
        """
        total_score = 0
        for text in texts:
            # Perform the model response using Ollama
            try:
                response = self.llm_chain({"question": text})
                confidence_score = response.get("confidence", 1.0)  # Use confidence if available
                total_score += -math.log(confidence_score)  # Log probability approximation
            except Exception as e:
                print_error(f"Error calculating approximate perplexity: {str(e)}",
                            app=Configuration.LANGCHAIN_QUEUE)
                return float("inf")
        
        return math.exp(total_score / len(texts)) if texts else float("inf")

    def execute_chain_query_with_metrics(self,
                                         categories: List[str],
                                         documents: List[str],
                                         user_query: str,
                                         expected_answer: str) -> dict:
        # Invoke model and get response
        result = self.execute_chain_query(categories, documents, user_query)
        generated_answer = result.get("RESPONSE") if result["STATE"] else ""
        
        # Define expected output for accuracy
        accuracy = self.calculate_accuracy([generated_answer], [expected_answer])
        
        # Mean Average Precision
        map_score = self.calculate_mean_average_precision([1], [1])  # Replace with actual relevance data if available
        
        # BERTScore
        bert_score_val = self.calculate_bertscore([generated_answer], [expected_answer])
        
        # Approximate Perplexity
        perplexity = self.calculate_approximate_perplexity([generated_answer])
        
        return {
            "response": result,
            "accuracy": accuracy,
            "map": map_score,
            "bertscore": bert_score_val,
            "perplexity": perplexity
        }

    def execute_chain_query(self,
                            categories: List[str],
                            documents: List[str],
                            user_query: str) -> dict:
        """Generate response using the Ollama model through LangChain."""
        query_prompt = {
            "question": user_query,
            "references": documents
        }
        
        try:
            # Using the Chain to invoke the Ollama model with the prompt
            result = self.llm_chain.invoke(query_prompt)
            return {
                "STATE": True,
                "RESPONSE": result
            }
        except Exception as e:
            print_error(message=f"Error in model execution: {str(e)}",
                        app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": False, "RESPONSE": None}
