import os
from typing import List
from devtools import debug
import asyncio
import lancedb
import logfire
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from openai import OpenAI
from tools.tokenizer import OpenAITokenizerWrapper
from tools.sitemap import get_sitemap_urls

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
model = os.getenv('MODEL', 'llama3.2:3b')
embedding_model = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)

# urls = ["https://arxiv.org/pdf/2408.09869"]
# urls = get_sitemap_urls("https://ds4sd.github.io/docling/")
urls = []
urls.extend(get_sitemap_urls("https://pydantic.dev"))
urls.extend(get_sitemap_urls("https://ai.pydantic.dev"))

debug(urls)

openai_client = OpenAI(
    base_url=base_url,
    api_key=api_key,
)

tokenizer = OpenAITokenizerWrapper()  # Load our custom tokenizer for OpenAI
MAX_TOKENS = 8191  # text-embedding-3-large's maximum context length

converter = DocumentConverter()

chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=MAX_TOKENS,
    merge_peers=True,
)

uri = "data/lancedb"
db = lancedb.connect(uri)


# Define a simplified metadata schema
class ChunkMetadata(LanceModel):
    """
    You must order the fields in alphabetical order.
    This is a requirement of the Pydantic implementation.
    """

    filename: str | None
    page_numbers: List[int] | None
    title: str | None


func = get_registry().get("openai").create(
    name=embedding_model,
    dim=embedding_dims,
    base_url=base_url,
    api_key=api_key,
)


class Chunks(LanceModel):
    text: str = func.SourceField()
    vector: Vector(embedding_dims) = func.VectorField()
    metadata: ChunkMetadata


async def main():
    table = db.create_table("docling", schema=Chunks, mode="overwrite")

    for result in converter.convert_all(urls):
        try:
            chunk_iter = chunker.chunk(dl_doc=result.document)
            chunks = list(chunk_iter)

            processed_chunks = [
                {
                    "text": chunk.text,
                    "metadata": {
                        "filename": chunk.meta.origin.filename,
                        "page_numbers": sorted(
                            {prov.page_no for item in chunk.meta.doc_items for prov in item.prov}
                        ) or None,
                        "title": chunk.meta.headings[0] if chunk.meta.headings else None,
                    },
                }
                for chunk in chunks
            ]

            table.add(processed_chunks)
        except Exception as e:
            print(e)

    table.to_pandas()
    table.count_rows()
    print("completed")


if __name__ == '__main__':
    asyncio.run(main())
