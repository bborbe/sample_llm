import asyncio
import os
import logfire
import streamlit as st
from devtools import debug
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart
from pydantic_ai.models.openai import OpenAIModel

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

# llama3.2:3b
# gemma2:9b
# gemma3:4b
# gemma3:12b
model_name = os.getenv('MODEL', "gemma3:12b")
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
