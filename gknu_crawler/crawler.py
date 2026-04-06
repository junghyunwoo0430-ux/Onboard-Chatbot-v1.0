import asyncio
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import sys

BASE_DOMAIN = "webonomics.co.kr"
START_URLS = [
    "https://webonomics.co.kr/",
    "https://webonomics.co.kr/web/m_main.php",
    "https://webonomics.co.kr/new/index.php",
]

MAX_CONCURRENCY = 100  # 동시 요청 개수 (속도 조절용)

visited = set()
results = []
sem = asyncio.Semaphore(MAX_CONCURRENCY)

def same_domain(url: str) -> bool:
    netloc = urlparse(url).netloc
    return netloc.endswith(BASE_DOMAIN)

def should_skip(url: str) -> bool:
    lower_url = url.lower()
    
    # Skip by file extension
    bad_ext = (".zip", ".pdf", ".jpg", ".jpeg", ".png", ".gif",
               ".mp4", ".avi", ".xls", ".xlsx", ".doc", ".docx")
    if any(lower_url.endswith(ext) for ext in bad_ext):
        return True
        
    # Skip by URL path or query patterns from user feedback
    bad_patterns = [
        "/bbs/",
        "password.php",
        "bo_table=",
        "wr_id="
    ]
    if any(pattern in lower_url for pattern in bad_patterns):
        return True
        
    return False

async def fetch(session: ClientSession, url: str) -> str | None:
    async with sem:  # 동시성 제한
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status >= 400:
                    return None
                return await resp.text()
        except Exception:
            return None

async def crawl_url(session: ClientSession, url: str, queue: asyncio.Queue):
    if url in visited or not same_domain(url) or should_skip(url):
        return
    visited.add(url)

    html = await fetch(session, url)
    if not html:
        return

    soup = BeautifulSoup(html, "html.parser")

    # Remove common boilerplate elements
    for selector in ["nav", "footer", "header", ".sidebar", ".menu", ".nav", ".footer", ".header"]:
        for element in soup.select(selector):
            element.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    text = soup.get_text(separator="\n", strip=True)

    results.append({
        "url": url,
        "title": title,
        "content": text,
    })

    for a in soup.find_all("a", href=True):
        next_url = urljoin(url, a["href"])
        if next_url not in visited and same_domain(next_url) and not should_skip(next_url):
            await queue.put(next_url)

async def worker(session: ClientSession, queue: asyncio.Queue):
    while True:
        url = await queue.get()
        try:
            await crawl_url(session, url, queue)
        finally:
            queue.task_done()

async def main():
    queue = asyncio.Queue()
    for u in START_URLS:
        await queue.put(u)

    async with aiohttp.ClientSession(headers={
        "User-Agent": "WebonomicsCrawler/1.0"
    }) as session:
        tasks = []
        for _ in range(MAX_CONCURRENCY):
            t = asyncio.create_task(worker(session, queue))
            tasks.append(t)

        await queue.join()

        for t in tasks:
            t.cancel()

    with open("webonomics_all_pages.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
