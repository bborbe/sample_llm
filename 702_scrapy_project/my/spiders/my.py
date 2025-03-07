from devtools import debug
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.http import Response
from typing import Generator


class MySpider(CrawlSpider):
    name = "my"
    allowed_domains = ["ai.pydantic.dev"]
    start_urls = ["https://ai.pydantic.dev"]
    rules = (
        Rule(LinkExtractor(allow=()), callback="parse_page", follow=True),
    )

    def parse_page(self, response: Response) -> Generator[dict, None, None]:
        print("url:", response.url)
        print("body.length:", len(response.body))
        debug(response)
        pass
