from devtools import debug
import lancedb
import logfire
from dotenv import load_dotenv

logfire.configure(send_to_logfire='if-token-present')
load_dotenv()

db = lancedb.connect(uri="data/lancedb")
table = db.open_table("docling")

num_results = 3
results = table.search('what is pydantic').limit(num_results).to_pandas()

debug(results)

# Print search results
print("\n🔍 **Search Results:**")
for x in range(0, len(results)):
    metadata = results.metadata[x]
    print(
        f'📌 {results.text[x]} '
        f'filename: {metadata["filename"]} '
        f'title: {metadata["title"]} '
        f'page_numbers: {metadata["page_numbers"]}'
    )
