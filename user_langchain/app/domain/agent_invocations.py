from user_langchain.prompt import prompt
from langchain_community.llms.ollama import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from tools.tools import tools
from utils.outputs import (print_error,
                           print_bold_message,
                           print_header_message,
                           print_warning_message)
from langchain_ms_config import Configuration

# TODO: validate task execution error responses to client in event architecture

class LangchainAgent:

    def __init__(self) -> None:
        self.llm_model = Ollama(model="llama3:70b-instruct-q2_K", base_url="http://localhost:11434")
        self._agent = create_react_agent(self.llm_model,
                                         tools,
                                         prompt)
        # TODO: Validate in depth agent executor
        self.agent_executor = AgentExecutor(
            agent=self._agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            return_intermediate_steps=True)

    @staticmethod
    def _invoke_query(executor, query, max_attempts=5):
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

        final_result = {"output": False,
                        "description": "Too many failed attempts"}
        for attempt in range(max_attempts):
            try:
                result = executor.invoke({"input": query,
                                          "max_tokens": 500})
                return {
                    "STATE": "PROCESSED",
                    "QUERY_MADE": query,
                    "RESPONSE": output_handler(result)
                }
            except Exception as e:
                print_error(message=f"Something failed: {e}",
                            app=Configuration.LANGCHAIN_QUEUE)

            print_warning_message(message=f"Attempt {attempt + 1}",
                                  app=Configuration.LANGCHAIN_QUEUE)
        return final_result

    def execute_agent_query(self, categories: list, documents: list, user_query: str):
        query_prompt = f"""
        Answer the following question based on the tools provided and references listed below.
        
        Question: {user_query}
        
        Categories: {categories}
        
        References for context: {documents}
        
        When answering, follow this strict format:

        1. Question: Restate the user's question.
        2. Thought: Explain your reasoning step-by-step.
        3. Action: Specify the action you will take (choose one from the tools provided).
        4. Action Input: Provide the exact input for the chosen action.
        5. Observation: Describe the result of the action.
        6. Thought: Reflect on the result to form a final conclusion.
        7. Final Answer: Provide a clear and concise final answer.

        Please ensure you follow this format without skipping any steps or labels.
        """

        print_header_message(message=f"Query prompt is: {query_prompt}", app=Configuration.LANGCHAIN_QUEUE)

        result = self._invoke_query(executor=self.agent_executor, query=f'{query_prompt}')

        if result['output']:
            print_bold_message(message=f"Query result is: {result}", app=Configuration.LANGCHAIN_QUEUE)
            return result
        else:
            print_error(message=f"Query failed: {result['description']}", app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}
