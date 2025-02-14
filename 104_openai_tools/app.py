import json
import os

from devtools import debug
import logfire
from dotenv import load_dotenv
from openai import OpenAI

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
model = os.getenv('MODEL', 'llama3.2:3b')

openai_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)


def get_weather(location: str) -> dict:
    weather_data = {
        "New York": {"temperature": "15°C", "condition": "Cloudy"},
        "London": {"temperature": "10°C", "condition": "Rainy"},
        "Tokyo": {"temperature": "18°C", "condition": "Sunny"},
    }
    return weather_data.get(location, {"error": "Location not found"})


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city name"},
                },
                "required": ["location"],
            },
        },
    }
]

system_prompt = ''
user_prompt = 'What is the weather in London?'

response = openai_client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    tools=tools,
    tool_choice="auto",
)
debug(response)

tool_calls = response.choices[0].message.tool_calls if response.choices else []
if tool_calls:
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        if function_name == "get_weather":
            result = get_weather(arguments["location"])
            print(f"Weather in {arguments['location']}: {result['temperature']} {result['condition']}")

else:
    print(response.choices[0].message.content)
