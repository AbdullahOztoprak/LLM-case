from __future__ import annotations

from pathlib import Path

from .config import Settings, get_settings
from .embeddings import HashEmbeddingClient, OllamaEmbeddingClient
from .generator import LocalGenerator
from .ingest import build_chunks
from .retriever import HybridRetriever
from .vector_store import JsonVectorStore


def make_embedding_client(
    settings: Settings | None = None,
    embedding_model: str | None = None,
):
    settings = settings or get_settings()
    if settings.use_ollama_embeddings:
        model = embedding_model or settings.embedding_model
        return OllamaEmbeddingClient(settings.ollama_base_url, model)
    return HashEmbeddingClient()


def load_retriever(
    index_file: Path | None = None,
    settings: Settings | None = None,
    embedding_model: str | None = None,
) -> HybridRetriever:
    settings = settings or get_settings()
    resolved_index_file = index_file or settings.index_file
    if not Path(resolved_index_file).exists():
        store = JsonVectorStore(resolved_index_file, HashEmbeddingClient())
        store.add(build_chunks(sample_only=True))
        store.persist()
    store = JsonVectorStore(
        resolved_index_file,
        make_embedding_client(settings, embedding_model=embedding_model),
    )
    return HybridRetriever(store)


def load_generator(settings: Settings | None = None) -> LocalGenerator:
    settings = settings or get_settings()
    return LocalGenerator(settings.ollama_base_url, settings.generation_model)
