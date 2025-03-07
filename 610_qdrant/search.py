import os

import logfire
import openai
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import SearchParams

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # text-embedding-3-small
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)

openai_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

# Initialize Qdrant client
qdrant = QdrantClient("localhost", port=6333)

# Collection Name
COLLECTION_NAME = "my_collection"


def get_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model=embedding_model,
    )
    return response.data[0].embedding


# 🔍 Search Query
query_text = "Future of AI in technology"
query_vector = get_embedding(query_text)

# Perform search in Qdrant
search_results = qdrant.search(
    collection_name=COLLECTION_NAME,
    query_vector=query_vector,
    limit=3,  # Get top 3 most similar results
    search_params=SearchParams(hnsw_ef=128, exact=False)  # Approximate search
)

# Print search results
print("\n🔍 **Search Results:**")
for result in search_results:
    print(f"📌 ID: {result.id}, Score: {result.score}, Text: {result.payload['text']}")
