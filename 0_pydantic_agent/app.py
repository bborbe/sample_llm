import os

import logfire
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from devtools import debug

logfire.configure(send_to_logfire='if-token-present')

load_dotenv()

model_name = os.getenv('MODEL', 'llama3.2:3b')
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'your-api-key')

model = OpenAIModel(
    model_name=model_name,
    base_url=base_url,
    api_key=api_key,
)

agent = Agent(
    model=model,
    retries=2,
)

if __name__ == '__main__':
    result = agent.run_sync('The windy city in the US of A.')
    debug(result)
    print(result.data)
    print(result.usage())
