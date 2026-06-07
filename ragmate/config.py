from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gemini_api_key: str
    api_key: str

    gemini_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"

    chroma_persist_dir: Path = Path("./chroma_data")
    upload_dir: Path = Path("./uploads")

    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_results: int = 5

    max_upload_mb: int = 20


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
