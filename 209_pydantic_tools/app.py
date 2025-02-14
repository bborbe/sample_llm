from __future__ import annotations as _annotations
import asyncio
import os
from typing import Any
import logfire
from devtools import debug
from dotenv import load_dotenv
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
model_name = os.getenv('MODEL', 'llama3.2:3b')

model = OpenAIModel(
    model_name,
    base_url=base_url,
    api_key=api_key,
)

weather_agent = Agent(
    model=model,
)


@weather_agent.tool_plain()
async def get_weather(location: str) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        location: The location to get the weather from.
    """
    weather_data = {
        "New York": {"temperature": "15°C", "condition": "Cloudy"},
        "London": {"temperature": "10°C", "condition": "Rainy"},
        "Tokyo": {"temperature": "18°C", "condition": "Sunny"},
    }
    result = weather_data.get(location)
    if not result:
        raise ModelRetry('Could not find the location')
    return result


async def main():
    result = await weather_agent.run(
        'What is the weather like in London and in Wiltshire?',
    )
    debug(result)
    print('Response:', result.data)


if __name__ == '__main__':
    asyncio.run(main())
