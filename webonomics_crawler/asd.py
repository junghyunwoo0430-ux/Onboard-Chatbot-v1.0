#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 RAG 지식 저장소 크롤러
- 웹사이트 전체 크롤링
- 완전 중복 제거 (해시 기반)
- RAG용 청크 생성
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib
import json
import re
import time
from typing import List, Dict, Set
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,  # 디버그 보고 싶으면 logging.DEBUG 로 바꾸기
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebonomicsCrawler:
    """
    사이트 크롤러 + RAG 지식 저장소 생성기

    기능:
    1. 전체 사이트 재귀적 크롤링
    2. 완전 중복 제거 (SHA-256 해시)
    3. RAG용 청크 분할
    4. JSON 저장
    """

    def __init__(self, base_url: str = "https://webonomics.co.kr/new/", delay: float = 0.5):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.delay = delay

        # 크롤링 상태 관리
        self.visited_urls: Set[str] = set()
        self.to_visit: Set[str] = {base_url}
        self.crawled_pages: List[Dict] = []

        # 중복 제거용
        self.content_hashes: Dict[str, str] = {}

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def normalize_url(self, url: str) -> str:
        """URL 정규화 - 트래킹 파라미터 제거, 경로 정리"""
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            params = parsed.query.split("&")
            clean_params = [p for p in params if not p.startswith("utm_")]
            if clean_params:
                normalized += f"?{'&'.join(clean_params)}"
        return normalized.rstrip("/")

    def is_same_domain(self, url: str) -> bool:
        """같은 도메인 체크"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain

    def extract_links(self, html: str, current_url: str) -> Set[str]:
        """HTML에서 모든 링크 추출"""
        soup = BeautifulSoup(html, "html.parser")
        links = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute_url = urljoin(current_url, href)
            normalized = self.normalize_url(absolute_url)

            if self.is_same_domain(normalized):
                links.add(normalized)

        return links

    def extract_content(self, html: str, url: str) -> Dict | None:
        """HTML에서 의미 있는 콘텐츠 추출"""
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
        content_text = soup.get_text(separator=" ", strip=True)
        content_text = re.sub(r"\s+", " ", content_text).strip()

        logger.debug(f"[DEBUG] URL: {url}")
        logger.debug(f"[DEBUG] Title: {title}")
        logger.debug(f"[DEBUG] Description: {description}")
        logger.debug(f"[DEBUG] Content length: {len(content_text)}")

        # 너무 짧은 페이지는 제외 (필요하면 기준 조절)
        if len(content_text) < 50:
            return None

        return {
            "url": url,
            "title": title,
            "description": description,
            "content": content_text,
            "length": len(content_text),
        }

    def calculate_content_hash(self, content: str) -> str:
        """SHA-256 해시로 완전 중복 검출"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def crawl(self) -> int:
        """전체 사이트 크롤링"""
        logger.info(f"🚀 {self.base_url} 크롤링 시작...")
        logger.info("=" * 70)

        page_count = 0
        error_count = 0

        while self.to_visit:
            url = self.to_visit.pop()

            if url in self.visited_urls:
                continue

            self.visited_urls.add(url)
            logger.info(f"📄 [{page_count + 1}] {url}")

            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()

                # 인코딩 자동 추론 사용
                response.encoding = response.apparent_encoding
                html_content = response.text

                # 콘텐츠 추출
                page_data = self.extract_content(html_content, url)

                if page_data is None:
                    logger.debug("   ⊘ 너무 짧은 콘텐츠 (< 50글자)")
                    continue

                # 완전 중복 확인
                content_hash = self.calculate_content_hash(page_data["content"])

                if content_hash in self.content_hashes:
                    logger.warning(
                        f"   ⚠️  완전 중복! 원본: {self.content_hashes[content_hash]}"
                    )
                    continue

                # 저장
                self.content_hashes[content_hash] = url
                self.crawled_pages.append(page_data)
                page_count += 1

                logger.info(f"   ✅ 저장됨 ({page_data['length']:,} 글자)")

                # 링크 추출 및 큐 업데이트
                links = self.extract_links(html_content, url)
                new_links = links - self.visited_urls
                self.to_visit.update(new_links)

                if new_links:
                    logger.info(f"   🔗 새 링크 {len(new_links)}개 발견")

                time.sleep(self.delay)

            except requests.exceptions.RequestException as e:
                logger.error(f"   ❌ 요청 오류: {type(e).__name__}: {str(e)[:80]}")
                error_count += 1
                continue
            except Exception as e:
                logger.error(f"   ❌ 예상치 못한 오류: {str(e)[:80]}")
                error_count += 1
                continue

        logger.info("=" * 70)
        logger.info("✅ 크롤링 완료!")
        logger.info(f"   📊 방문한 URL: {len(self.visited_urls)}개")
        logger.info(f"   📄 저장된 페이지: {len(self.crawled_pages)}개")
        logger.info(f"   ❌ 오류: {error_count}개")

        return len(self.crawled_pages)

    def remove_duplicates(self) -> List[Dict]:
        """완전 중복 콘텐츠 제거"""
        logger.info("\n🔄 중복 콘텐츠 정제 중...")
        logger.info("=" * 70)

        unique_pages: Dict[str, Dict] = {}
        duplicate_count = 0

        for page in self.crawled_pages:
            content_hash = self.calculate_content_hash(page["content"])

            if content_hash not in unique_pages:
                unique_pages[content_hash] = page
            else:
                duplicate_count += 1
                logger.info(f"🗑️  제거 (완전 중복): {page['title'][:40]}")

        cleaned_pages = list(unique_pages.values())

        logger.info("=" * 70)
        logger.info("정제 결과:")
        logger.info(f"   원본 페이지: {len(self.crawled_pages)}개")
        logger.info(f"   정제 후: {len(cleaned_pages)}개")
        logger.info(f"   제거된 중복: {duplicate_count}개")

        return cleaned_pages

    def save_to_json(self, pages: List[Dict], filename: str = "webonomics_rag_knowledge.json") -> str:
        """RAG 지식 저장소를 JSON으로 저장"""
        rag_data = {
            "metadata": {
                "source": self.base_url,
                "total_documents": len(pages),
                "crawl_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "description": "RAG 지식 저장소",
            },
            "documents": pages,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(rag_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 저장 완료: {filename}")
        return filename

    def create_rag_chunks(
        self,
        pages: List[Dict],
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> List[Dict]:
        """
        RAG 시스템용 텍스트 청크 생성

        Args:
            pages: 문서 리스트
            chunk_size: 청크의 단어 수
            overlap: 청크 간 겹치는 단어 수
        """
        chunks: List[Dict] = []
        chunk_id = 0

        for page in pages:
            full_text = f"[{page['title']}]\n{page['description']}\n\n{page['content']}"
            words = full_text.split()

            step = chunk_size - overlap
            for i in range(0, len(words), step):
                chunk_words = words[i : i + chunk_size]

                if len(chunk_words) < 50:
                    continue

                chunk_text = " ".join(chunk_words)

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "source_url": page["url"],
                        "source_title": page["title"],
                        "chunk_text": chunk_text,
                        "chunk_length": len(chunk_words),
                    }
                )

                chunk_id += 1

        logger.info(f"\n✂️  RAG 청크 생성 완료: {len(chunks)}개")
        return chunks

    def save_chunks_to_json(self, chunks: List[Dict], filename: str = "webonomics_rag_chunks.json") -> str:
        """청크를 JSON으로 저장"""
        chunks_data = {
            "metadata": {
                "total_chunks": len(chunks),
                "chunk_size": 500,
                "overlap": 50,
                "description": "LLM 임베딩 및 벡터 저장소용 청크",
            },
            "chunks": chunks,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 청크 저장 완료: {filename}")
        return filename


def main():
    """메인 실행 함수"""

    crawler = WebonomicsCrawler(
        base_url="https://webonomics.co.kr/new/",
        delay=0.5,
    )

    # 1️⃣ 크롤링
    page_count = crawler.crawl()

    if page_count == 0:
        logger.warning("크롤링된 페이지가 없습니다.")
        return

    # 2️⃣ 중복 제거
    cleaned_pages = crawler.remove_duplicates()

    # 3️⃣ RAG 지식 저장소 저장
    crawler.save_to_json(cleaned_pages)

    # 4️⃣ RAG 청크 생성
    chunks = crawler.create_rag_chunks(cleaned_pages, chunk_size=500, overlap=50)

    # 5️⃣ 청크 저장
    crawler.save_chunks_to_json(chunks)

    # 📊 최종 요약
    logger.info("\n" + "=" * 70)
    logger.info("🎉 RAG 지식 저장소 생성 완료!")
    logger.info("=" * 70)
    logger.info("📁 생성된 파일:")
    logger.info("   1. webonomics_rag_knowledge.json (정제된 문서)")
    logger.info("   2. webonomics_rag_chunks.json (임베딩용 청크)")
    logger.info("\n📊 통계:")
    logger.info(f"   - 수집한 페이지: {len(crawler.visited_urls)}개")
    logger.info(f"   - 저장된 문서: {len(cleaned_pages)}개")
    logger.info(f"   - 생성된 청크: {len(chunks)}개")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
