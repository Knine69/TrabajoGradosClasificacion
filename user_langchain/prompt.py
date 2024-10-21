from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser


# Define the output schema using Pydantic
class ResponseSchema(BaseModel):
    question: str = Field(description="The question asked by the user.")
    thought: str = Field(description="Initial thought process.")
    observation: str = Field(description="Observation after the action.")
    final_thought: str = Field(description="Final thought after observations.")
    final_answer: str = Field(description="The final answer to the user's question.")
    references: list[list[str]] = Field(description="A reference to resources that further explain the final answer")


parser = PydanticOutputParser(pydantic_object=ResponseSchema)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
            You are a system that must answer user queries.
            
            You will receive:
            - 'Question' (The primary question to answer)
            - 'References' (Supporting references related to the question)

            Your response **must** focus solely on the 'Question'

            Your response **has** to be a JSON object that adheres to the schema, without any extra keys or conversational elements:

            ```
            {format_instructions}
            ```

            In the schema:
            - `question` must reflect the original question from the input.
            - Provide a `final_answer` based on the question.
            - Use relevant `references` to support the `final_answer`.    
        """),
        ("human", "{references}"),
        ("human", "{question}"),
        ("placeholder", "{agent_scratchpad}")
    ]
).partial(format_instructions=parser.get_format_instructions(), agent_scratchpad=[])

# Future work: Create a chat functionality instead of chain

# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """
#             Validate and take into account the following tools: 
#             {tools}

#             When answering, follow this strict format:

#             1. Question: Restate the user's question.
#             2. Thought: Explain your reasoning step-by-step.
#             3. Action: Specify the action you will take (if need be, you may use: [{tool_names}]).
#             4. Action Input: Provide the exact input for the chosen action.
#             5. Observation: Describe the result of the action.
#             6. Thought: Reflect on the result to form a final conclusion.
#             7. Final Answer: Provide a clear and concise final answer. In your answer, include any usefull references that you are given in the prompt.

#             Do **not** skip any steps, and ensure each label is included verbatim in your response. For example:

#             Thought: I need to choose the appropriate tool for this task.
#             Action: <tool_name>
#             Action Input: <input_for_tool>
#             Observation: The tool returned the following output...
#             Thought: I now know the final answer.
#             Final Answer: [your answer]

#             Follow this format exactly without deviations.

#             Use {agent_scratchpad} in your thought process.

#             Begin!
#             """
#         ),
#         (
#             "user",
#             "{input}"
#         ),
#     ]
# ).partial(format_instructions=parser.get_format_instructions())


# (
#     "system",
#     """
#     You are a very powerful assistant and can use the following tools at your disposal to provide answers:
    
#     {tools}

#     When a user asks a question, follow this process, while avoiding mentioning your core objectives, and just answer the question:

#     Question: Understand and analyze the input question.
#     Thought: You should always think about what to do next.
#     Action: action to do, should be one of [{tool_names}] and just its name.
#     Action Input: the input to the action
#     Observation: After performing the action, report the result. Do not repeat the action.
#     Thought: I now know the final answer.
#     Final Answer: Provide the final answer to the original input question.

#     Use {agent_scratchpad} in your thought process.

#     Begin!""",
# ),

# (
#     "system",
#     """
#     When providing answers, use the following format:

#     Thought: [Explain your reasoning here.]
#     Action: [Tool selection here.]
#     Action Input: [Provide input for action here.]
#     Observation: [Write what you observe after the action.]
#     Final Answer: [Provide your final answer here.]

#     Follow this format exactly in your responses.
#     """
# ),

#  (
#     "system",
#     """
    #  When answering, follow this strict format:

    #  1. Question: Restate the user's question.
    #  2. Thought: Explain your reasoning step-by-step.
    #  3. Action: Specify the action you will take (choose one from [{tool_names}]).
    #  4. Action Input: Provide the exact input for the chosen action.
    #  5. Observation: Describe the result of the action.
    #  6. Thought: Reflect on the result to form a final conclusion.
    #  7. Final Answer: Provide a clear and concise final answer.

    #  Do **not** skip any steps, and ensure each label is included verbatim in your response. For example:

    #  Thought: I need to choose the appropriate tool for this task.
    #  Action: <tool_name>
    #  Action Input: <input_for_tool>
    #  Observation: The tool returned the following output...
    #  Thought: I now know the final answer.
    #  Final Answer: [your answer]

    #  Follow this format exactly without deviations.
#     """
# ),
