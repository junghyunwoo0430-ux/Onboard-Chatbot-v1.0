from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")


def resolve_path(raw_path: str, relative_to: Path = BASE_DIR) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (relative_to / path).resolve()


def split_csv(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def get_faiss_path() -> Path:
    return resolve_path(os.getenv("FAISS_PATH", "faiss_index"))


def get_embedding_model() -> str:
    return os.getenv("EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")


def get_llm_base_url() -> str:
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip()
    if not llm_base_url:
        raise ValueError("LLM_BASE_URL is not set. Check rag_system/.env or container environment variables.")
    return llm_base_url


def get_openai_api_key() -> str:
    return os.getenv("OPENAI_API_KEY", "not-needed")


def get_cors_origins() -> list[str]:
    origins = split_csv(os.getenv("CORS_ORIGINS", "*"))
    return origins or ["*"]


def get_retriever_k() -> int:
    return int(os.getenv("RETRIEVER_K", "5"))


def get_context_max_chars() -> int:
    return int(os.getenv("CONTEXT_MAX_CHARS", "4000"))


def get_api_prefix() -> str:
    raw_prefix = os.getenv("API_PREFIX", "/v1").strip() or "/v1"
    if not raw_prefix.startswith("/"):
        raw_prefix = f"/{raw_prefix}"
    return raw_prefix.rstrip("/") or "/v1"


def get_data_paths() -> list[Path]:
    raw_paths = split_csv(os.getenv("DATA_PATHS"))
    if raw_paths:
        return [resolve_path(raw_path, PROJECT_ROOT) for raw_path in raw_paths]

    return [
        PROJECT_ROOT / "webonomics_chunked.jsonl",
        PROJECT_ROOT / "pdf_chunked.jsonl",
    ]
