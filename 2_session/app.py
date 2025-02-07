import streamlit as st
import ollama
from pydantic import BaseModel

# model = "codellama:13b"
model = "gemma2:9b"
# model = "llama3.1:8b"
# model = "llama3.2:3b"

# Define a structured response model
class AIResponse(BaseModel):
    reply: str

# Streamlit UI
st.set_page_config(page_title="Local AI Chat", layout="wide")
st.title("💬 Local AI Chatbot with Ollama")

# Chat history
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

    # Query the local AI model with full chat history
    response = ollama.chat(
        model=model,
        messages=st.session_state.messages,  # Pass entire conversation
    )

    try:
        # Validate response with Pydantic
        structured_response = AIResponse(reply=response['message']['content'])
        bot_reply = structured_response.reply
    except Exception:
        bot_reply = "Sorry, I had trouble understanding that."

    # Append AI response to chat
    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    with st.chat_message("assistant"):
        st.markdown(bot_reply)
