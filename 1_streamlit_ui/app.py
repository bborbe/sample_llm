import asyncio
import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from devtools import debug

# model_name = "gemma2:9b"
model_name = "llama3.2:3b"

agent = Agent(
    OpenAIModel(
        model_name,
        base_url='http://localhost:11434/v1',
        api_key='your-api-key',
    ),
    retries=2,
)


async def main():
    st.title("Ai Agent")

    input = st.text_input("Input:")

    if st.button("Go"):
        if input:
            response = await agent.run(
                user_prompt=input,
            )
            debug(response)
            st.write("Result:")
            st.write(response.data)
        else:
            st.warning("Please enter something")


if __name__ == "__main__":
    asyncio.run(main())
