# gknu_crawler/gknu_crawler/spiders/webonomics_spider.py
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime
from ..utils import extract_main_text

class WebonomicsSpider(CrawlSpider):
    name = "webonomics"
    allowed_domains = ["webonomics.co.kr"]
    start_urls = ["https://webonomics.co.kr/new/index.php"]

    rules = (
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                unique=True,
            ),
            callback="parse_page",
            follow=True,
        ),
    )

    def parse_page(self, response):
        title = (response.xpath("//title/text()").get() or "").strip()
        text = extract_main_text(response.text)

        yield {
            "url": response.url,
            "title": title,
            "published_at": None,
            "fetched_at": datetime.now().isoformat(),
            "source": "webonomics_crawl",
            "text": text,
        }
