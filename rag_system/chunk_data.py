import json
import re
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import PROJECT_ROOT

INPUT_PATH = PROJECT_ROOT / "webonomics_all_pages.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "webonomics_chunked.jsonl"
BOILERPLATE_PATTERNS = [
    r"Loading the content\.\.\.",
    r"Loading depends on your connection speed!",
    r"Social Network Facebook Blog",
    r"Webonomics Co\.,Ltd\. All rights reserved\.",
]


def normalize_text(text: str) -> str:
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    normalized = "\n".join(lines)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def chunk_data(input_path: Path = INPUT_PATH, output_path: Path = OUTPUT_PATH) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Crawled data file not found: {input_path}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )

    chunked_records = []

    print(f"Reading data from {input_path}...")
    with input_path.open("r", encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)
            content = record.get("content", "")
            metadata = {
                "source": record.get("url", ""),
                "title": record.get("title", ""),
            }

            if not content:
                continue

            content = normalize_text(content)
            if not content:
                continue

            chunks = text_splitter.split_text(content)
            for index, chunk in enumerate(chunks):
                chunked_records.append(
                    json.dumps(
                        {
                            "content": chunk,
                            "metadata": {**metadata, "chunk": index},
                        },
                        ensure_ascii=False,
                    )
                )

    print(f"Writing {len(chunked_records)} chunks to {output_path}...")
    with output_path.open("w", encoding="utf-8") as file:
        for record in chunked_records:
            file.write(record + "\n")

    print("Chunking complete.")


if __name__ == "__main__":
    chunk_data()
