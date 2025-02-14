import json
import os

import asyncio
from devtools import debug
import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
model = os.getenv('MODEL', 'gemma2:9b')

openai_client = AsyncOpenAI(
    base_url=base_url,
    api_key=api_key,
)


async def main() -> None:
    system_prompt = ''
    user_prompt = 'Who are you?'

    response = await openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )
    debug(response)
    print(response.choices[0].message.content)


if __name__ == "__main__":
    asyncio.run(main())
