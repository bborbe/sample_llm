from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
import streamlit as st


class StreamHandler(BaseCallbackHandler):
    """Custom callback handler for streaming LLM responses to the UI."""
    def __init__(self, container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Appends new tokens to the container in real time."""
        self.text += token
        self.container.markdown(self.text)


def initialize_session_state():
    """Initializes the session state for storing messages."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            ChatMessage(role="assistant", content="How can I help you?")
        ]


def display_chat_history():
    """Displays the chat history from the session state."""
    for msg in st.session_state.messages:
        st.chat_message(msg.role).write(msg.content)


def handle_user_input():
    """Handles user input and processes the LLM response."""
    if prompt := st.chat_input():
        # Append user's message
        st.session_state.messages.append(ChatMessage(role="user", content=prompt))
        st.chat_message("user").write(prompt)

        # Set up assistant response container and handler
        with st.chat_message("assistant"):
            container = st.empty()
            stream_handler = StreamHandler(container)

            # Configure LLM
            llm = ChatOpenAI(
                api_key="ollama",
                model="gemma2:9b",
                base_url="http://localhost:11434/v1",
                streaming=True,
                callbacks=[stream_handler],
            )

            # Get LLM response
            response = llm(st.session_state.messages)

            # Append assistant's message
            st.session_state.messages.append(
                ChatMessage(role="assistant", content=response.content)
            )
            container.markdown(response.content)


# Main application flow
def main():
    initialize_session_state()
    display_chat_history()
    handle_user_input()


if __name__ == "__main__":
    main()
