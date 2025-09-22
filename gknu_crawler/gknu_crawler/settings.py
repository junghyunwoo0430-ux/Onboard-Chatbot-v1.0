# gknu_crawler/gknu_crawler/settings.py
BOT_NAME = "gknu_crawler"

SPIDER_MODULES = ["gknu_crawler.spiders"]
NEWSPIDER_MODULE = "gknu_crawler.spiders"

ROBOTSTXT_OBEY = True            # robots.txt 준수
CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 0
AUTOTHROTTLE_ENABLED = False
#AUTOTHROTTLE_START_DELAY = 0.5
#AUTOTHROTTLE_MAX_DELAY = 5

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "gknu-crawler/1.0 (+research; contact=you@example.com)"
}

# 바이너리/큰파일 무시
MEDIA_ALLOW_REDIRECTS = False

# 출력: JSON Lines & CSV 두 가지 예시 (원하는 것만 남기세요)
FEEDS = {
    "outputs/gknu_chatbot_data.jsonl": {"format": "jsonlines", "encoding": "utf8", "overwrite": True},
    "outputs/gknu_chatbot_data.csv": {"format": "csv", "encoding": "utf8", "overwrite": True},
}