import asyncio

import logfire
from devtools import debug
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

logfire.configure(send_to_logfire='if-token-present')

# model_name = "mistral:7b"
model_name = "llama3.2:3b"

support_agent = Agent(
    OpenAIModel(
        model_name=model_name,
        base_url='http://localhost:11434/v1',
        api_key='your-api-key',
    ),
    retries=2,
)


@support_agent.tool_plain
async def banana(a: int, b: int) -> int:
    """
    Banana takes two numbers and calclates a result based on them.
    """
    return int(a + b)


async def main():
    result = await support_agent.run('call banana(2,7) for me')
    # debug(result)
    print(result.data)

    result = await support_agent.run('calc following formular (23 + 42 + 1337) for me')
    # debug(result)
    print(result.data)


if __name__ == "__main__":
    asyncio.run(main())
