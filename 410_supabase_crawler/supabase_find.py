import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from devtools import debug
from supabase import Client, create_client
import asyncio
from typing import List

load_dotenv()

embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # text-embedding-3-small
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'your-api-key')
user_query = 'what is up?'

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)
openai_client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url,
)


async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model=embedding_model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error


async def main():
    # Get the embedding for the query
    query_embedding = await get_embedding(user_query)

    # Query Supabase for relevant documents
    result = supabase.rpc(
        'match_site_pages',
        {
            'query_embedding': query_embedding,
            'match_count': 5,
            'filter': {'source': 'pydantic_ai_docs'}
        }
    ).execute()

    if not result.data:
        return "No relevant documentation found."

    debug(result.data)


if __name__ == '__main__':
    asyncio.run(main())
