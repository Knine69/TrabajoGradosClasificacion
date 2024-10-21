from user_langchain.prompt import ResponseSchema, prompt, parser
from langchain_community.llms import Ollama
from langchain.chains.base import Chain
from utils.outputs import (print_error,
                           print_successful_message,
                           print_header_message,
                           print_warning_message)
from langchain_ms_config import Configuration
import json

# TODO: validate task execution error responses to client in event architecture

class LangchainAgent:
    def __init__(self):
        self.llm_model = Ollama(model="llama3.2", base_url="http://localhost:11434")
        # Set up the agent executor
        self.llm_chain = prompt | self.llm_model


    @staticmethod
    def _invoke_query(executor: Chain, query, max_attempts=5):
        final_result = {"output": False,
                        "description": "Too many failed attempts"}
        for attempt in range(max_attempts):
            try:
                result = executor.invoke({"input": query,
                                          "max_tokens": 1000})
                result: ResponseSchema = parser.parse(result)
                return {
                    "STATE": "PROCESSED",
                    "QUERY_MADE": query,
                    "RESPONSE": result
                }
            except Exception as e:
                print_error(message=f"Something failed: {e}",
                            app=Configuration.LANGCHAIN_QUEUE)

            print_warning_message(message=f"Attempt {attempt + 1}",
                                  app=Configuration.LANGCHAIN_QUEUE)
        return final_result

    def execute_chain_query(self, categories: list,  documents: list, user_query: str):
        
        query_prompt = f"""
Question: {user_query}
References: {documents}
        """
        
        print_header_message(message=f"Query prompt is: {query_prompt}", app=Configuration.LANGCHAIN_QUEUE)

        result = self._invoke_query(executor=self.llm_chain, query=f'{query_prompt}')

        if result['STATE']:
            
            print_successful_message(
                message=f"Query result is: {result['RESPONSE'].model_dump_json(indent=2)}",
                app=Configuration.LANGCHAIN_QUEUE)
            
            result['RESPONSE'] = result['RESPONSE'].model_dump()
            return result
        else:
            print_error(message=f"Query failed: {result['description']}", app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}


if __name__ == "__main__":
    agent = LangchainAgent()
    result = agent.execute_chain_query([], ["Some data for RAG", "Some other data for RAG"], "What is an action?")
