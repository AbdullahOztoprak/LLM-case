from pathlib import Path

from devdocs_rag.embeddings import HashEmbeddingClient
from devdocs_rag.ingest import build_chunks
from devdocs_rag.retriever import HybridRetriever
from devdocs_rag.vector_store import JsonVectorStore


def test_hybrid_retriever_finds_expected_sample_source(tmp_path: Path):
    store = JsonVectorStore(tmp_path / "index.json", HashEmbeddingClient())
    store.add(build_chunks(sample_only=True, chunk_size=80, chunk_overlap=10))
    retriever = HybridRetriever(store)

    results = retriever.search("How do I create a pull request from a fork?", top_k=3)

    assert results
    assert results[0].chunk.metadata["source"] == "github_docs"


def test_source_filter_limits_results(tmp_path: Path):
    store = JsonVectorStore(tmp_path / "index.json", HashEmbeddingClient())
    store.add(build_chunks(sample_only=True, chunk_size=80, chunk_overlap=10))
    retriever = HybridRetriever(store)

    results = retriever.search("path parameters", top_k=3, source_filter=["fastapi_docs"])

    assert results
    assert all(result.chunk.metadata["source"] == "fastapi_docs" for result in results)
