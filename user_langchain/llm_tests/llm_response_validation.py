from typing import List
from bert_score import score
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer, util
from langchain_community.llms.ollama import Ollama
from langchain.chains.base import Chain
from user_langchain.prompt import prompt, parser
import json
import spacy


test_data = {
    "documents": [
        ["a person who designs buildings and oversees their construction.", "a professional who plans and supervises large structural projects"],
        ["an electronic device that processes data, performing calculations and tasks.", "a programmable machine that can execute a set of instructions."],
        ["an animal known for its loyalty and often referred to as 'man's best friend.'", "a domesticated mammal, often used as a pet or for security."],
        ["a large celestial body that orbits a star, usually spherical in shape.", "an object in space that revolves around a star, like the planets in our solar system."],
        ["a substance consumed to provide nutritional support for the body.", "material taken in by organisms to sustain life and provide energy."],
        ["a system that transports blood throughout the body, consisting of the heart and blood vessels.", "the heart pumps blood through a network of arteries, veins, and capillaries."],
        ["a written or spoken story, often involving fictional characters and events.", "a tale or account that entertains, informs, or conveys a moral lesson."],
        ["a legal binding agreement between two or more parties.", "a formal arrangement that outlines the terms and conditions agreed upon by the parties involved."],
        ["a practice that involves physical postures, breathing techniques, and meditation.", "an ancient discipline aimed at promoting physical, mental, and spiritual well-being."],
        ["a tool used to amplify or record sound, typically used in performances or recordings.", "an electronic device that converts sound into an electrical signal."],
        ["a vehicle designed for transporting goods or people over land.", "a motorized machine used for transportation, such as a car, truck, or bus."],
        ["an area where animals and plants live together in their natural environment.", "a specific place where a particular organism or community of organisms lives."],
        ["a period of 24 hours starting at midnight, used as a unit of time.", "the time it takes for Earth to complete one full rotation on its axis."],
        ["a piece of software used to browse and interact with content on the internet.", "a program that allows users to access and view websites."],
        ["a method of encoding data into a format that is unreadable without a decryption key.", "a technique used to secure data by converting it into a secret code."],
        ["a financial gain, usually the difference between the amount earned and the amount spent.", "the positive return on an investment or business activity after expenses."],
        ["an object in space made of ice, dust, and gas, with a bright tail when near the sun.", "a celestial body that appears as a bright ball with a trailing stream of particles."],
        ["a literary genre that focuses on imaginative and futuristic concepts, like space exploration and time travel.", "a category of fiction often dealing with advanced science and technology."],
        ["a large muscle located at the back of your lower leg, helping with movements like walking or running.", "the muscle in the calf that connects the heel to the back of the knee."],
        ["a form of precipitation consisting of ice crystals that fall from the sky in cold weather.", "frozen water vapor that forms delicate, white flakes and falls to the ground."]
  
    ],
    "user_queries": [
        "What is an architect?",
        "What is a computer?",
        "What is a dog?",
        "What is a planet?",
        "What is food?",
        "What is the circulatory system?",
        "What is a narrative?",
        "What is a contract?",
        "What is yoga?",
        "What is a microphone?",
        "What is a vehicle?",
        "What is a habitat?",
        "What is a day?",
        "What is a web browser?",
        "What is encryption?",
        "What is profit?",
        "What is a comet?",
        "What is science fiction?",
        "What is the calf muscle?",
        "What is snow?"
    ],
    "expected_answers": [
        "An architect is a person who designs buildings and supervises their construction.",
        "A computer is an electronic device that processes data and performs calculations.",
        "A dog is a domesticated animal known for its loyalty and companionship.",
        "A planet is a large celestial body that orbits a star.",
        "Food is a substance consumed to provide energy and nutrients to the body.",
        "The circulatory system is the system that transports blood throughout the body.",
        "A narrative is a story or account of events and experiences.",
        "A contract is a legally binding agreement between two or more parties.",
        "Yoga is a practice that combines physical postures, breathing, and meditation for well-being.",
        "A microphone is a device used to amplify or record sound.",
        "A vehicle is a machine used for transporting people or goods over land.",
        "A habitat is an area where animals and plants live in their natural environment.",
        "A day is a period of 24 hours, the time it takes for Earth to rotate once on its axis.",
        "A web browser is a software program used to access and view websites on the internet.",
        "Encryption is a method of converting data into a secure code to prevent unauthorized access.",
        "Profit is the financial gain obtained when revenue exceeds expenses.",
        "A comet is an object in space made of ice and dust that develops a bright tail when near the sun.",
        "Science fiction is a genre of literature that explores imaginative concepts like advanced technology.",
        "The calf muscle is a large muscle in the lower leg that helps with movements like walking or running.",
        "Snow is frozen water vapor that forms ice crystals and falls from the sky in cold weather."
    
        
    ]
}


class LlmResponseValidator:
    def __init__(self):
        self.llm_model = Ollama(model="llama3:70b",
                                base_url="http://localhost:11434",
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