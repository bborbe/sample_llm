import os

import logfire
import openai
from openai import OpenAI

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # text-embedding-3-small
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)

qdrant = QdrantClient("localhost", port=6333)

openai_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

COLLECTION_NAME = "my_collection"

qdrant.delete_collection(COLLECTION_NAME, timeout=60)
qdrant.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={
        "size": embedding_dims,
        "distance": "Cosine",
    }
)


def get_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model=embedding_model,
    )
    return response.data[0].embedding


# Sample data
documents = [
    "Quantum computing is the future of technology.",
    "Artificial intelligence is transforming industries.",
    "Space exploration is advancing rapidly."
]

# Convert documents to embeddings
points = [
    PointStruct(
        id=i,
        vector=get_embedding(doc),
        payload={"text": doc},
    )
    for i, doc in enumerate(documents)
]

# Upload embeddings to Qdrant
qdrant.upsert(collection_name=COLLECTION_NAME, points=points)

print("Embeddings successfully added to Qdrant!")
