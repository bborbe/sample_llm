from httpx import AsyncClient
import streamlit as st
import asyncio
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.messages import UserPromptPart, ModelRequest, ModelResponse, ModelResponsePart, SystemPromptPart, \
    TextPart
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
    st.title("Pydantic AI Chatbot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message("human" if isinstance(msg, ModelRequest) else "ai"):
            st.markdown(msg.parts[0].content)

    if prompt := st.chat_input("What would you like research today?"):
        st.chat_message("user").markdown(prompt)

        response_content = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            async with agent.run_stream(
                    user_prompt=prompt,
                    message_history=st.session_state.messages,
            ) as result:
                async for message in result.stream_text(delta=True):
                    response_content += message
                    message_placeholder.markdown(response_content)

                debug(result)
                st.session_state.messages = result.all_messages()
                st.session_state.messages.append(ModelResponse(
                    parts=[
                        TextPart(
                            content=response_content,
                            part_kind='text',
                        ),
                    ],
                    timestamp=result.timestamp(),
                    kind='response',
                ))


if __name__ == "__main__":
    asyncio.run(main())
