# gknu_crawler/gknu_crawler/utils.py
from __future__ import annotations
import re
from datetime import datetime, timezone
from dateutil import tz
import dateparser
import trafilatura
from w3lib.html import remove_tags

SEOUL = tz.gettz("Asia/Seoul")

META_DATE_XPATHS = [
    "//meta[@property='article:published_time']/@content",
    "//meta[@name='date']/@content",
    "//meta[@name='pubdate']/@content",
    "//meta[@property='og:updated_time']/@content",
    "//meta[@name='lastmod']/@content",
    "//time/@datetime",
    "//span[contains(@class, 'date')]/text()",
    "//div[contains(@class, 'date')]/text()",
]

def parse_when(texts: list[str]) -> datetime | None:
    for t in texts:
        if not t:
            continue
        dt = dateparser.parse(
            t.strip(),
            settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Asia/Seoul"},
        )
        if dt:
            return dt.astimezone(SEOUL)
    return None

def extract_main_text(html: str) -> str:
    # trafilatura로 본문 요약 추출 (실패 시 태그 제거한 평문)
    extracted = trafilatura.extract(html, include_comments=False, include_tables=True)
    if extracted:
        return extracted.strip()
    return remove_tags(html).strip()

def within_years(dt: datetime | None, years: int = 2) -> bool:
    if not dt:
        return True  # 날짜가 없으면 일단 수집(후처리에서 걸러도 됨)
    now = datetime.now(SEOUL)
    cutoff = now.replace(tzinfo=SEOUL)  # 보정
    try:
        cutoff = cutoff.replace(year=now.year - years)
    except ValueError:
        # 2/29 등의 경계 케이스
        cutoff = cutoff - (now - now.replace(year=now.year - years))
    return dt >= cutoff
