# gknu_crawler/gknu_crawler/spiders/sitemap_recent.py
import scrapy
from scrapy.spiders import SitemapSpider
from datetime import datetime
from ..utils import META_DATE_XPATHS, parse_when, extract_main_text, within_years

class GKNUSitemapRecentSpider(SitemapSpider):
    name = "gknu_sitemap_recent"

    # ✅ 실제 도메인으로 바꿔주세요
    allowed_domains = ["gknu.ac.kr", "www.gknu.ac.kr"]
    sitemap_urls = [
        "https://www.gknu.ac.kr/sitemap.xml",
        "https://www.gknu.ac.kr/sitemap_index.xml",
    ]
    # 필요 시 하위 사이트맵 패턴 추가
    # sitemap_follow = [r"post", r"notice", r"news"]

    def sitemap_filter(self, entries):
        # <lastmod> 기반 선(先)필터 (없으면 모두 통과)
        for entry in entries:
            lastmod = entry.get("lastmod")
            if lastmod:
                dt = parse_when([lastmod])
                if within_years(dt, years=2):
                    yield entry
            else:
                yield entry

    def parse(self, response):
        # 메타/본문/날짜 파싱
        sel = response.xpath
        title = (sel("//title/text()").get() or "").strip()
        meta_dates = [d.get() for d in (response.xpath(x) for x in META_DATE_XPATHS) for d in d]
        published_at = parse_when(meta_dates)

        # 2년 제한
        if not within_years(published_at, years=2):
            return

        text = extract_main_text(response.text)

        yield {
            "url": response.url,
            "title": title,
            "published_at": published_at.isoformat() if published_at else None,
            "fetched_at": datetime.now().isoformat(),
            "source": "sitemap",
            "text": text,
        }
