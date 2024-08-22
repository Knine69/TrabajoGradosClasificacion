from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a very powerful assistant and can use the following tools at your disposal to provide answers:
            {tools}

            When a user asks a question, follow this process:

            Question: Understand and analyze the input question.
            Thought: You should always think about what to do next.
            Action: action to do, should be one of [{tool_names}] and just its name.
            Action Input: the input to the action
            Observation: After performing the action, report the result. Do not repeat the action.
            Thought: I now know the final answer.
            Final Answer: Provide the final answer to the original input question.

            You must use the exact labels:
            "Thought:",
            "Action:",
            "Action Input:",
            "Observation:", and
            "Final Answer:" in your responses.

            Ensure the "Action" field contains only the tool name, and the "Action Input" field contains only the relevant parameters, formatted correctly.

            Use {agent_scratchpad} in your thought process.

            Begin!""",
        ),
        (
            "user",
            "{input}"
        ),
    ]
)