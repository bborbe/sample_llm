import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from devtools import debug

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

api_key = os.getenv('GEMINI_API_KEY', 'missing')

model_name = os.getenv('MODEL', 'gemini-2.0-flash')
model = GeminiModel(
    model_name=model_name,
    provider='google-gla',
    api_key=api_key,
)

agent = Agent(
    model=model,
)

if __name__ == '__main__':
    result = agent.run_sync('The windy city in the US of A.')
    debug(result)
    print(result.data)
    print(result.usage())
