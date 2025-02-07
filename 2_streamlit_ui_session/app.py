import asyncio

import logfire
import streamlit as st
from devtools import debug
from pydantic_ai import Agent
from pydantic_ai.messages import ModelResponse, ModelRequest
from pydantic_ai.models.openai import OpenAIModel

logfire.configure(send_to_logfire='if-token-present')

model_name = "gemma2:9b"
# model_name = "llama3.2:3b"

model = OpenAIModel(
    model_name,
    base_url='http://localhost:11434/v1',
    api_key='your-api-key',
)

agent = Agent(
    model=model,
    retries=2,
)


async def main():
    st.set_page_config(page_title="Local AI Chat", layout="wide")
    st.title("💬 Local AI Chatbot")

    if "history" not in st.session_state:
        st.session_state.history = []

    for msg in st.session_state.history:
        if isinstance(msg, ModelRequest):
            with st.chat_message("user"):
                st.markdown(msg.parts[0].content)
        elif isinstance(msg, ModelResponse):
            with st.chat_message("assistant"):
                st.markdown(msg.parts[0].content)

    user_input = st.chat_input("Ask me anything...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        result = await agent.run(
            user_prompt=user_input,
            message_history=st.session_state.history,
        )
        debug(result)
        st.session_state.history = result.all_messages()

        with st.chat_message("assistant"):
            st.markdown(result.data)


if __name__ == '__main__':
    asyncio.run(main())
