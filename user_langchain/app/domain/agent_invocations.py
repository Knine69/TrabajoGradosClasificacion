from user_langchain.prompt import prompt
from langchain_community.llms.ollama import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from tools.tools import tools


class LangchainAgent:

    def __init__(self) -> None:
        self.llm_model = Ollama(model="llama3:70b-instruct-q2_K")
        # self.llm_model = Ollama(model="llama3:70b-instruct")
        # self.llm_model = Ollama(model="llava:13b")
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
                print(f"Something failed: {e}")

            print(f"Attempt {attempt + 1}")
        return final_result

    def execute_agent_query(self,
                            categories: list,
                            documents: list,
                            user_query: str):
        query_prompt = f"""
        Responde la siguiente pregunta, en caso de ser una pregunta, o 
        referencia información asociada a la siguiente consulta: {user_query}
        
        Considera a qué categoria puede asociarse la pregunta y tu respuesta,
        a partir de las siguientes categorias:
        {categories}
        
        Finalmente, si necesitas hacer referencias sobre la información para
        responder, puedes basarte en los siguientes documentos: {documents}
        """

        result = self._invoke_query(executor=self.agent_executor,
                                    query=f'{query_prompt}')

        if result['output']:
            print(f"Query result is: {result}")
            return result
        else:
            print(f"Query failed: {result['description']}")
            return {"STATE": "ERROR", "DESCRIPTION": result['description']}
