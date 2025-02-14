from __future__ import annotations as _annotations
import asyncio
import os
import logfire
from devtools import debug
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.settings import ModelSettings
from typing import Dict

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('LLM_API_KEY', 'no-llm-api-key-provided')
model_name = os.getenv('MODEL', 'llama3.1:8b')

model = OpenAIModel(
    model_name,
    base_url=base_url,
    api_key=api_key,
)

weather_agent = Agent(
    model=model,
    model_settings=ModelSettings(
        temperature=0.0
    ),
    system_prompt="Be concise, reply with one sentence.",
)


class Weather(BaseModel):
    temperature: str
    condition: str


class WeatherNotFound(BaseModel):
    error: str


@weather_agent.tool_plain()
async def get_weather(location: str) -> Weather | WeatherNotFound:
    """Get the weather at a location.

    Args:
        location: The location to get the weather from.
    """
    weather_data: Dict[str, Weather] = {
        "New York": Weather(temperature="15°C", condition="Cloudy"),
        "London": Weather(temperature="10°C", condition="Rainy"),
        "Tokyo": Weather(temperature="18°C", condition="Sunny"),
    }
    return weather_data.get(location, WeatherNotFound(error="Location not found"))


async def main():
    result = await weather_agent.run(
        user_prompt='What is the weather like in London and in Wiltshire?',
    )
    debug(result)
    print('Response:', result.data)


if __name__ == '__main__':
    asyncio.run(main())
