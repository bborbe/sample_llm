import asyncio
from devtools import debug
import lancedb
import logfire
from dotenv import load_dotenv

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

uri = "data/lancedb"
db = lancedb.connect(uri)
table = db.open_table("docling")


def get_context(query: str, num_results: int = 3) -> str:
    """Search the database for relevant context.

    Args:
        query: User's question
        num_results: Number of results to return

    Returns:
        str: Concatenated context from relevant chunks with source information
    """
    results = table.search(query).limit(num_results).to_pandas()
    debug(results)
    contexts = []

    for _, row in results.iterrows():
        # Extract metadata
        filename = row["metadata"]["filename"]
        page_numbers = row["metadata"]["page_numbers"]
        title = row["metadata"]["title"]

        # Build source citation
        source_parts = []
        if filename:
            source_parts.append(filename)
        if page_numbers:
            source_parts.append(f"p. {', '.join(str(p) for p in page_numbers)}")

        source = f"\nSource: {' - '.join(source_parts)}"
        if title:
            source += f"\nTitle: {title}"

        contexts.append(f"{row['text']}{source}")

    return "\n\n".join(contexts)


async def main():
    print(get_context('What is pydantic about?'))


if __name__ == '__main__':
    asyncio.run(main())
