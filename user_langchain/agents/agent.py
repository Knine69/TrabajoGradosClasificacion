from user_langchain.prompt import prompt
from langchain_community.llms.ollama import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from tools.tools import tools


class LangchainAgent:

    def __init__(self) -> None:
        self.llm_model = Ollama(model="llama3")
        self._agent = create_react_agent(self.llm_model,
                                         tools,
                                         prompt)
        self.agent_executor = AgentExecutor(
            agent=self._agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            # callbacks=m, TODO: Validate if behaviour can be corrected with
            # callbacks
            return_intermediate_steps=True)

    def invoke_query(self, executor, query, max_attempts=5):
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

        for attempt in range(max_attempts):
            try:
                result = executor.invoke({"input": query})
                return {
                    'query_made': query,
                    'output': output_handler(result)
                    }
            except Exception as e:
                print(f"Something failed: {e}")
            print(f"Attempt {attempt + 1}")
        return {"output": False, "description": "Too many failed attempts"}

    def execute_agent_query(self):
        query_prompt = "Cuál es la longitud de la palabra: "
        query = input(f"{query_prompt}")
        result = self.invoke_query(executor=self.agent_executor,
                                   query=f'{query_prompt}"{query}"')

        if result['output']:
            print(f"Query result is: {result}")
        else:
            print(f"Query failed: {result['description']}")


if __name__ == "__main__":
    agent = LangchainAgent()
    agent.execute_agent_query()
