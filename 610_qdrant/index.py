import logging
import os
from qdrant_client.http.models import PointStruct
from tools.tokenizer import OpenAITokenizerWrapper
import logfire
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from tools.sitemap import get_sitemap_urls

logging.basicConfig(level=logging.WARN)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")  # text-embedding-3-small
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)

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
logger.info(f'found {len(urls)} to index')

idx = 0
for url in urls:
    logger.debug(f'process url {url} started')
    result = converter.convert(url)
    try:
        chunk_iter = chunker.chunk(dl_doc=result.document)
        chunks = list(chunk_iter)
        logger.info(f'chunk size: {len(chunks)}')

        embedding_results = openai_client.embeddings.create(
            input=[chunk.text for chunk in chunks],
            model=embedding_model,
        )

        points = []
        for page_number, (embedding, chunk) in enumerate(zip(embedding_results.data, chunks)):
            idx += 1
            points.append(
                PointStruct(
                    id=idx,
                    vector=embedding.embedding,
                    payload={
                        "url": url,
                        "text": chunk.text,
                        "filename": chunk.meta.origin.filename,
                        "page_number": page_number,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                    },
                )
            )
            logger.info(f'points {idx} completed')
        qdrant_client.upsert(COLLECTION_NAME, points)
        logger.info(f'insert {len(points)} for url {url} completed')

    except Exception as e:
        logger.info(f'process url {url} failed: {e}')
    finally:
        logger.debug(f'process url {url} completed')

logger.info(f'indexed {len(urls)} urls with {idx} points completed')
