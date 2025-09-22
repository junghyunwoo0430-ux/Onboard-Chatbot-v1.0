# gknu_crawler/gknu_crawler/spiders/crawl_recent.py
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from datetime import datetime
from ..utils import META_DATE_XPATHS, parse_when, extract_main_text, within_years

class GKNUCrawlRecentSpider(CrawlSpider):
    name = "gknu_crawl_recent"

    # ✅ 실제 도메인으로 바꿔주세요 (필요시 하위 서브도메인 추가)
    allowed_domains = ["gknu.ac.kr", "www.gknu.ac.kr", "notice.gknu.ac.kr", "news.gknu.ac.kr"]

    # ✅ 시작 URL을 게시판/공지/뉴스 메인 등으로 확장하세요
    start_urls = [
        "https://www.gknu.ac.kr/main/index.do",
    ]

    custom_settings = {
        # 이미지/파일 등은 따라가지 않음
        "DUPEFILTER_DEBUG": False,
    }

    rules = (
        # 챗봇에 불필요한 'fund', 'news' 등의 링크는 제외하고,
        # '대학안내', '학과소개', '학사정보', '공지사항'과 관련된 페이지만 수집하도록 설정
        Rule(
            LinkExtractor(
                allow_domains=allowed_domains,
                # deny 키워드를 추가하여 불필요한 페이지 제외
                deny=(
                    r'ipsi', r'fund', r'news', r'login', r'join', r'member', r'search',
                    # 파일 확장자도 여기서 한 번 더 거부
                    r'\.jpg', r'\.jpeg', r'\.png', r'\.gif', r'\.bmp', r'\.svg', r'\.webp',
                    r'\.zip', r'\.rar', r'\.7z', r'\.tar', r'\.gz',
                    r'\.mp4', r'\.mp3', r'\.wav', r'\.avi', r'\.mov',
                    r'\.ppt', r'\.pptx', r'\.xls', r'\.xlsx', r'\.doc', r'\.docx', r'\.pdf',
                ),
                deny_extensions=[], # deny 규칙으로 옮겼으므로 비워둠
                unique=True,
            ),
            callback="parse_page",
            follow=True,
        ),
    )

    def parse_page(self, response):
        sel = response.xpath
        title = (sel("//title/text()").get() or "").strip()

        # 게시판 전용 날짜 선택자(예: 공지/뉴스의 리스트·상세 구조)를 추가로 커스터마이즈 해도 좋습니다.
        meta_dates = [d.get() for x in META_DATE_XPATHS for d in response.xpath(x)]
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
            "source": "crawl",
            "text": text,
        }
