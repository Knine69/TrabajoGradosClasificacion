from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Validate and take into account the following tools: 
            {tools}

            When answering, follow this strict format:

            1. Question: Restate the user's question.
            2. Thought: Explain your reasoning step-by-step.
            3. Action: Specify the action you will take (if need be, you may use: [{tool_names}]).
            4. Action Input: Provide the exact input for the chosen action.
            5. Observation: Describe the result of the action.
            6. Thought: Reflect on the result to form a final conclusion.
            7. Final Answer: Provide a clear and concise final answer. In your answer, include any usefull references that you are given in the prompt.

            Do **not** skip any steps, and ensure each label is included verbatim in your response. For example:

            Thought: I need to choose the appropriate tool for this task.
            Action: <tool_name>
            Action Input: <input_for_tool>
            Observation: The tool returned the following output...
            Thought: I now know the final answer.
            Final Answer: [your answer]

            Follow this format exactly without deviations.

            Use {agent_scratchpad} in your thought process.

            Begin!
            """
        ),
        (
            "user",
            "{input}"
        ),
    ]
)
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
