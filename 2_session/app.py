import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from devtools import debug
import streamlit as st
from pydantic_ai.messages import (
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

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
    st.set_page_config(page_title="Local AI Chat", layout="wide")
    st.title("💬 Local AI Chatbot with Ollama")

    # Chat history
    if "history" not in st.session_state:
        st.session_state.history = []
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Ask me anything...")

    if user_input:
        # Append user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        result = await agent.run(
            user_prompt=user_input,
            message_history=st.session_state.history,
        )
        debug(result)
        st.session_state.history = result.all_messages()

        # Append AI result to chat
        st.session_state.messages.append({"role": "assistant", "content": result.data})
        with st.chat_message("assistant"):
            st.markdown(result.data)


if __name__ == '__main__':
    asyncio.run(main())
