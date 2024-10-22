from user_langchain.prompt import ResponseSchema, prompt, parser
from langchain_community.llms import Ollama
from langchain.chains.base import Chain
from utils.outputs import (print_error,
                           print_successful_message,
                           print_header_message,
                           print_warning_message)
from langchain_ms_config import Configuration
from pydantic_core import ValidationError
import re

# TODO: validate task execution error responses to client in event architecture

class LangchainChain:
    def __init__(self):
        self.llm_model = Ollama(model="llama3:70b", base_url="http://localhost:11434")
        # self.llm_model = Ollama(model="llama3.2:latest", base_url="http://localhost:11434")
        # Set up the agent executor
        self.llm_chain = prompt | self.llm_model

    
    def preprocess_json_string(json_string: str):
        """
        Preprocesses a JSON-like string to ensure it is valid JSON.
        - Adds missing quotes around values where necessary.
        - Replaces None with null.
        - Ensures references are in list format.
        """
        # Replace None with null
        json_string = json_string.replace("None", "null")


        return json_string
    
    @staticmethod
    def _invoke_query(executor: Chain, query, max_attempts=5):
        final_result = {"STATE": False,
                        "DESCRIPTION": "Too many failed attempts"}
        for attempt in range(max_attempts):
            try:
                llm_result = executor.invoke({"question": query['question'],
                                          "references": query['references'],
                                          "max_tokens": 1000})
                print_header_message(message=f"Response: {llm_result}",
                                     app=Configuration.LANGCHAIN_QUEUE)
                llm_result_str = LangchainChain.preprocess_json_string(str(llm_result))
                return {
                    "STATE": True,
                    "QUERY_MADE": query,
                    "RESPONSE": llm_result_str
                }
            except Exception as e:
                print_error(message=f"Something failed: {str(e)}",
                            app=Configuration.LANGCHAIN_QUEUE)
            except ValidationError as e:
                print_error(message=f"Wrong response schema detected: {str(e)}",
                            app=Configuration.LANGCHAIN_QUEUE)

            print_warning_message(message=f"Attempt {attempt + 1}",
                                  app=Configuration.LANGCHAIN_QUEUE)
        return final_result

    def execute_chain_query(self, categories: list,  documents: list, user_query: str):
        
        query_prompt = {
            "question": user_query,
            "references": documents
        }
        
        print_header_message(message=f"Query prompt is: {query_prompt}", app=Configuration.LANGCHAIN_QUEUE)

        result = self._invoke_query(executor=self.llm_chain, query=query_prompt)

        if result['STATE']:
            
            print_successful_message(
                message=f"Query result is: {result['RESPONSE']}",
                app=Configuration.LANGCHAIN_QUEUE)
            
            result['RESPONSE'] = result['RESPONSE']
            return result
        else:
            print_error(message=f"Query failed: {result['description']}", app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}


if __name__ == "__main__":
    agent = LangchainChain()
    result = agent.execute_chain_query([], ["Some data for RAG", "Some other data for RAG"], "What is an action?")
