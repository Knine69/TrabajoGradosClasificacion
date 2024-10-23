from pydantic import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.structured import ResponseSchema 
from langchain.output_parsers.structured import StructuredOutputParser


# Define the output schema using Pydantic

# Define each field of the response schema
response_schemas = [
    ResponseSchema(name="question", description="The question asked by the user."),
    ResponseSchema(name="answer", description="The final answer to the user's question."),
    ResponseSchema(name="references", description="A reference list to resources that further justify the final answer")
]

# Use StructuredOutputParser to parse the response
parser = StructuredOutputParser(response_schemas=response_schemas)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
            You are a system that must answer user queries.
            
            You will receive:
            - 'Question' (The primary question to answer)
            - 'References' (Supporting references related to the question)

            Your response **must** focus primarily and foremost on the 'Question'. 
            It **must** also include relevant information from 'References' in your final answer.

            Your response **necessarily must** adhere strictly to the schema below.

            {format_instructions}

            **Ensure** that your response explicitly contains:
            - 'question' must reflect the original input question.
            - 'answer' must address the question directly.
            - 'references' must be based on the provided references ({references}) to support the 'final_answer'. Present them in APA citation format.
            
            Remember that for every answer, you **MUST** justify yourself using one or more references and they need to have their own paragraph.
        """),
        ("human", "{references}"),
        ("human", "{question}"),
        ("placeholder", "{agent_scratchpad}")
    ]
).partial(agent_scratchpad=[])

# Future work: Create a chat functionality instead of chain
