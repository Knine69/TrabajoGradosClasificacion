from user_langchain.prompt import prompt, parser
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
                                          "max_tokens": 1000})
                result = parser.parse(result)
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

    def execute_agent_query(self, categories: list,  documents: list, user_query: str):
        query_prompt = prompt.format(user_query=user_query, documents=documents)

        # query_prompt = f"""
        # Question: {user_query}
        # References for context: {documents}
        
        # Present your answer in the format of: 
        # 1. Question: {user_query}
        # 2. Thought:
        # 3. Action:
        # 4. Action Input:
        # 5. Observation:
        # 6. Thought:
        # 7. Final Answer:

        # """

        print_header_message(message=f"Query prompt is: {query_prompt}", app=Configuration.LANGCHAIN_QUEUE)

        result = self._invoke_query(executor=self.agent_executor, query=f'{query_prompt}')

        if result['output']:
            print_bold_message(message=f"Query result is: {result}", app=Configuration.LANGCHAIN_QUEUE)
            return result
        else:
            print_error(message=f"Query failed: {result['description']}", app=Configuration.LANGCHAIN_QUEUE)
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}
