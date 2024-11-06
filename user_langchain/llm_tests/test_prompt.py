from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.structured import ResponseSchema 
from langchain.output_parsers.structured import StructuredOutputParser


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", """
            You are a system that must answer user queries.
            
            You will receive:
            - 'Question' (The question to answer)
            - 'References' (Information to complement your responses)

            Your response **must** focus primarily and foremost on the 'Question'.
            
            You may use references comming from 'References
        """),
        ("human", "{question}"),
        ("human", "{references}"),
        ("placeholder", "{agent_scratchpad}")
    ]
).partial(agent_scratchpad=[])