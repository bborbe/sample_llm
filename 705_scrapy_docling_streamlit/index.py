import os
from typing import List
import lancedb
import logfire
from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from dotenv import load_dotenv
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from openai import OpenAI
from tools.tokenizer import OpenAITokenizerWrapper
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

base_url = os.getenv('BASE_URL', 'http://localhost:11434/v1')
api_key = os.getenv('API_KEY', 'no-llm-api-key-provided')
model = os.getenv('MODEL', 'llama3.2:3b')
embedding_model = os.getenv('EMBEDDING_MODEL', 'nomic-embed-text')
embedding_dims = os.getenv('EMBEDDING_DIMS', 768)

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
    name="nomic-embed-text",
    dim=embedding_dims,
    base_url=base_url,
    api_key=api_key,
)


class Chunks(LanceModel):
    text: str = func.SourceField()
    vector: Vector(embedding_dims) = func.VectorField()
    metadata: ChunkMetadata


table = db.create_table("docling", schema=Chunks, mode="overwrite")


class MySpider(CrawlSpider):
    name = "my"
    allowed_domains = ["ai.pydantic.dev"]
    start_urls = ["https://ai.pydantic.dev"]
    rules = (
        Rule(LinkExtractor(allow=()), callback="parse_page", follow=True),
    )

    def parse_page(self, response: Response):
        result = converter.convert(response.url)
        print(f'parse_page {response.url} started')
        try:
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
                for chunk in chunker.chunk(dl_doc=result.document)
            ]

            table.add(processed_chunks)
        except Exception as e:
            print(e)
        print(f'parse_page {response.url} completed')


# ✅ Running CrawlSpider with CrawlerProcess
process = CrawlerProcess(settings={
    "LOG_LEVEL": "WARN",
    # "LOG_LEVEL": "INFO",
    # "LOG_LEVEL": "DEBUG",
    "USER_AGENT": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "ROBOTSTXT_OBEY": False,
    #    "FEEDS": {"output.json": {"format": "json"}},  # Save results in JSON
})

process.crawl(MySpider)
process.start()
print("completed")
