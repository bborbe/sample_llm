import os

from qdrant_client.http.models import PointStruct

from tools.tokenizer import OpenAITokenizerWrapper
import logfire
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # text-embedding-3-small
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)
from tools.sitemap import get_sitemap_urls

converter = DocumentConverter()

openai_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

COLLECTION_NAME = "my_collection"

qdrant_client = QdrantClient(
    location="localhost",
    port=6333,
)
qdrant_client.delete_collection(COLLECTION_NAME, timeout=60)
qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config={
        "size": embedding_dims,
        "distance": "Cosine",
    }
)

tokenizer = OpenAITokenizerWrapper()  # Load our custom tokenizer for OpenAI
MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=MAX_TOKENS,
    merge_peers=True,
)


def get_embedding(text):
    response = openai_client.embeddings.create(
        input=text,
        model=embedding_model,
    )
    return response.data[0].embedding


# urls = ["https://arxiv.org/pdf/2408.09869"]
# urls = get_sitemap_urls("https://ds4sd.github.io/docling/")
urls = []
urls.extend(get_sitemap_urls("https://pydantic.dev"))
urls.extend(get_sitemap_urls("https://ai.pydantic.dev"))

for result in converter.convert_all(urls):
    try:
        chunk_iter = chunker.chunk(dl_doc=result.document)
        chunks = list(chunk_iter)
        texts = [
            chunk.text for chunk in chunks
        ]

        # metadatas = [
        #     {
        #         "filename": chunk.meta.origin.filename,
        #         "page_numbers": sorted(
        #             {prov.page_no for item in chunk.meta.doc_items for prov in item.prov}
        #         ) or None,
        #         "title": chunk.meta.headings[0] if chunk.meta.headings else None,
        #     } for chunk in chunks
        # ]
        embedding_result = openai_client.embeddings.create(
            input=texts,
            model=embedding_model,
        )
        points = [
            PointStruct(
                id=idx,
                vector=data.embedding,
                payload={
                    "text": text,
                },
            )
            for idx, (data, text) in enumerate(zip(embedding_result.data, texts))
        ]
        qdrant_client.upsert(COLLECTION_NAME, points)

    except Exception as e:
        print(e)

print("completed")
