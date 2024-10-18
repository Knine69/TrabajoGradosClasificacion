from user_langchain.prompt import prompt, parser
from langchain.llms import Ollama
from langchain.agents import AgentExecutor, BaseSingleActionAgent
from utils.outputs import (print_error,
                           print_bold_message,
                           print_header_message,
                           print_warning_message)
from langchain_ms_config import Configuration

# TODO: validate task execution error responses to client in event architecture


# class SimpleRetriever(LlamaIndexRetriever):

#     def __init__(self, documents: list):
#         self.documents = documents

#     def retrieve(self, query: str) -> list:
#         results = [doc for doc in self.documents if any(word in doc for word in query.split())]
#         return results


class LangchainAgent:

    def __init__(self) -> None:
        self.llm_model = Ollama(model="llama3:70b-instruct-q2_K", base_url="http://localhost:11434")

        self.agent = BaseSingleActionAgent(
            llm=self.llm_model,
            prompt=prompt,
            verbose=True
        )

        self.agent_executor = AgentExecutor(
            agent=self.agent,
            verbose=True,
            output_parser=parser,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True
        )

    @staticmethod
    def _invoke_query(executor: AgentExecutor, query, max_attempts=5):
        final_result = {"output": False,
                        "description": "Too many failed attempts"}
        for attempt in range(max_attempts):
            try:
                result = executor.run({"input": query,
                                          "max_tokens": 1000})
                result = parser.parse(result)
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

    def execute_agent_query(self, categories: list,  documents: list, user_query: str):
        
        query_prompt = f"""
            Question: {user_query}
            References: {documents}
        """
        
        print_header_message(message=f"Query prompt is: {query_prompt}", app=Configuration.LANGCHAIN_QUEUE)

        result = self._invoke_query(executor=self.agent_executor, query=f'{query_prompt}')

        if result['output']:
            print_bold_message(message=f"Query result is: {result}", app=Configuration.LANGCHAIN_QUEUE)
            return result
        else:
            print_error(message=f"Query failed: {result['description']}", app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}
