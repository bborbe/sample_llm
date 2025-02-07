import asyncio
import streamlit as st
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from devtools import debug

model = OpenAIModel(
    "gemma2:9b",
    base_url='http://localhost:11434/v1',
    api_key='your-api-key',
)

agent = Agent(
    model,
    retries=2,
)
async def main():
    st.title("Ai Agent")

    input = st.text_input("Input:")

    if st.button("Go"):
        if input:
            response = await agent.run(input)
            debug(response)
            st.write("Result:")
            st.write(response.data)
        else:
            st.warning("Please enter something")



if __name__ == "__main__":
    asyncio.run(main())
