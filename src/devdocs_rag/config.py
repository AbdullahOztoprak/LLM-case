from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    generation_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"
    chroma_dir: Path = Path("data/chroma")
    index_file: Path = Path("data/generated/sample_index.json")
    top_k: int = 5
    retrieval_mode: str = "hybrid"
    chunk_size: int = 700
    chunk_overlap: int = 120
    use_ollama_embeddings: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
