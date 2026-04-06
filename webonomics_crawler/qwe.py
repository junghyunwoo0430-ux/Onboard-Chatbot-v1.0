#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
웨보노믹스 RAG 지식 저장소 크롤러 (초고속 aiohttp 버전)
- 병렬 HTTP 요청 (aiohttp)
- 완전 중복 제거 (SHA-256)
- 전체 페이지 크롤링
- RAG용 청크 생성
- 결과물을 단일 파일(webonomics_crawler_data.json)에 저장
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import json
import re
import time
from typing import List, Dict, Set
import logging

# ------------------------------
# 로깅 설정
# ------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ===========================================================
# 🚀 초고속 Webonomics 크롤러 클래스
# ===========================================================
class FastWebonomicsCrawler:
    def __init__(
        self,
        base_url: str = "https://webonomics.co.kr/new/",
        max_tasks: int = 100
    ):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc

        # 크롤링 상태
        self.visited_urls: Set[str] = set()
        self.to_visit: asyncio.Queue = asyncio.Queue()
        self.to_visit.put_nowait(base_url)
        self.crawled_pages: List[Dict] = []

        # 중복 제거용
        self.content_hashes: Dict[str, str] = {}

        # 동시 요청 개수
        self.max_tasks = max_tasks

        # User-Agent
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    # -------------------------------------------
    # URL 정규화
    # -------------------------------------------
    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if parsed.query:
            params = parsed.query.split("&")
            clean_params = [p for p in params if not p.startswith("utm_")]
            if clean_params:
                normalized += f"?{'&'.join(clean_params)}"

        return normalized.rstrip("/")

    # -------------------------------------------
    # 같은 도메인인지 체크
    # -------------------------------------------
    def is_same_domain(self, url: str) -> bool:
        return urlparse(url).netloc == self.domain

    # -------------------------------------------
    # HTML 내 링크 추출
    # -------------------------------------------
    def extract_links(self, html: str, current_url: str) -> Set[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute = urljoin(current_url, href)
            normalized = self.normalize_url(absolute)

            if self.is_same_domain(normalized):
                links.add(normalized)

        return links

    # -------------------------------------------
    # HTML 콘텐츠 추출
    # -------------------------------------------
    def extract_content(self, html: str, url: str):
        soup = BeautifulSoup(html, "html.parser")

        # 제목
        title = "No Title"
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.h1:
            title = soup.h1.get_text(strip=True)

        # 메타 설명
        description = ""
        meta_desc = soup.find("meta", {"name": "description"})
        if meta_desc:
            description = meta_desc.get("content", "").strip()

        # 전체 텍스트 추출
        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text)

        if len(text) < 50:  # 너무 짧으면 제외
            return None

        return {
            "url": url,
            "title": title,
            "description": description,
            "content": text,
            "length": len(text)
        }

    # -------------------------------------------
    # 해시 계산(중복 제거)
    # -------------------------------------------
    def hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    # -------------------------------------------
    # 병렬 워커
    # -------------------------------------------
    async def worker(self, session: aiohttp.ClientSession):
        while True:
            try:
                url = self.to_visit.get_nowait()
            except asyncio.QueueEmpty:
                return

            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            logger.info(f"📄 방문 → {url}")

            try:
                async with session.get(url, headers=self.headers, timeout=10) as resp:
                    if resp.status != 200:
                        continue

                    html = await resp.text()

                    # 콘텐츠 추출
                    page = self.extract_content(html, url)
                    if page is None:
                        continue

                    # 중복 검사
                    h = self.hash_content(page["content"])
                    if h in self.content_hashes:
                        continue

                    # 저장
                    self.content_hashes[h] = url
                    self.crawled_pages.append(page)

                    # 링크 추출 후 큐에 넣기
                    for link in self.extract_links(html, url):
                        if link not in self.visited_urls:
                            self.to_visit.put_nowait(link)

            except Exception as e:
                logger.error(f"❌ 에러: {e}")

    # -------------------------------------------
    # 메인 크롤링 시작
    # -------------------------------------------
    async def crawl(self):
        logger.info("🚀 aiohttp 초고속 크롤링 시작!")

        async with aiohttp.ClientSession() as session:
            workers = [
                asyncio.create_task(self.worker(session))
                for _ in range(self.max_tasks)
            ]
            await asyncio.gather(*workers)

        logger.info("🎉 크롤링 완료!")
        logger.info(f"📊 방문한 URL: {len(self.visited_urls)}개")
        logger.info(f"📄 저장된 페이지: {len(self.crawled_pages)}개")

    # -------------------------------------------
    # RAG 청크 생성
    # -------------------------------------------
    def create_rag_chunks(self, pages: List[Dict], chunk_size=500, overlap=50):
        chunks = []
        cid = 0

        for p in pages:
            full = f"[{p['title']}]\n{p['description']}\n\n{p['content']}"
            words = full.split()

            step = chunk_size - overlap
            for i in range(0, len(words), step):
                chunk_words = words[i:i + chunk_size]
                if len(chunk_words) < 50:
                    continue

                chunks.append({
                    "chunk_id": cid,
                    "source_url": p["url"],
                    "source_title": p["title"],
                    "chunk_text": " ".join(chunk_words),
                    "chunk_length": len(chunk_words)
                })

                cid += 1

        logger.info(f"✂️ RAG 청크 생성 완료 → {len(chunks)}개")
        return chunks


# ===========================================================
# 🚀 main() — 최종 단일 JSON 생성
# ===========================================================
def main():
    crawler = FastWebonomicsCrawler(
        base_url="https://webonomics.co.kr/new/",
        max_tasks=100  # 동시 요청 수 (속도 핵심)
    )

    # 크롤링
    asyncio.run(crawler.crawl())

    # RAG 청크 생성
    chunks = crawler.create_rag_chunks(crawler.crawled_pages)

    # 결과물 단일 JSON 저장
    output = {
        "metadata": {
            "source": crawler.base_url,
            "crawl_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_documents": len(crawler.crawled_pages),
            "total_chunks": len(chunks),
        },
        "documents": crawler.crawled_pages,
        "chunks": chunks
    }

    filename = "webonomics_crawler_data.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("🎉 전체 처리 완료!")
    logger.info(f"📁 생성된 파일: {filename}")


# ===========================================================
# 실행 엔트리
# ===========================================================
if __name__ == "__main__":
    main()
