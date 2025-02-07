import asyncio
import streamlit as st
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel


# Define Pydantic model for input validation
class UserInput(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500, title="User Prompt")


model = OpenAIModel(
    'llama3.1:8b',
    base_url='http://localhost:11434/v1',
    api_key='your-api-key',
)

agent = Agent(
    model,
    # 'Be concise, reply with one sentence.' is enough for some models (like openai) to use
    # the below tools appropriately, but others like anthropic and gemini require a bit more direction.
    system_prompt=(
        'Be concise, reply with one sentence.'
        'Use the `get_lat_lng` tool to get the latitude and longitude of the locations, '
        'then use the `get_weather` tool to get the weather.'
    ),
    retries=2,
)

async def main():

    # Streamlit UI
    st.title("AI Agent with Streamlit and Pydantic")
    st.write("Enter a prompt below and get a response from the AI.")

    # User input
    txt_input = st.text_area("Enter your prompt:")

    if st.button("Generate Response"):
        try:
            # Validate input with Pydantic
            user_input = UserInput(prompt=txt_input)
            response = await agent.run(
                user_input.prompt
            )
            st.write("### AI Response:")
            st.write(response)
        except Exception as e:
            st.error(f"Invalid input: {str(e)}")


if __name__ == '__main__':
    asyncio.run(main())