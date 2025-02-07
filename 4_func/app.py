import asyncio
from dataclasses import dataclass

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelResponse, ModelRequest
from pydantic_ai.models.openai import OpenAIModel
from devtools import debug
import streamlit as st

logfire.configure(send_to_logfire='if-token-present')

model_name = "llama3.1:8b"


class DatabaseConn:
    """This is a fake database for example purposes.

    In reality, you'd be connecting to an external database
    (e.g. PostgreSQL) to get information about customers.
    """

    @classmethod
    async def customer_name(cls, *, id: int) -> str | None:
        if id == 123:
            return 'John'

    @classmethod
    async def customer_balance(cls, *, id: int, include_pending: bool) -> float:
        if id == 123:
            return 123.45
        else:
            raise ValueError('Customer not found')


@dataclass
class SupportDependencies:
    customer_id: int
    db: DatabaseConn


agent = Agent(
    OpenAIModel(
        model_name,
        base_url='http://localhost:11434/v1',
        api_key='your-api-key',
    ),
    deps_type=SupportDependencies,
    retries=2,
)


@agent.tool
async def customer_balance(
        ctx: RunContext[SupportDependencies], include_pending: bool
) -> str:
    """Returns the customer's current account balance."""
    balance = await ctx.deps.db.customer_balance(
        id=ctx.deps.customer_id,
        include_pending=include_pending,
    )
    return f'${balance:.2f}'


async def main():
    deps = SupportDependencies(customer_id=123, db=DatabaseConn())

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
            deps=deps,
        )
        debug(result)
        st.session_state.history = result.all_messages()

        with st.chat_message("assistant"):
            st.markdown(result.data)


if __name__ == '__main__':
    asyncio.run(main())
