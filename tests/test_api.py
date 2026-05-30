from fastapi.testclient import TestClient

from devdocs_rag.api import app
from devdocs_rag.models import Answer, Chunk, RetrievedChunk

client = TestClient(app)


def test_models_returns_fallback_when_ollama_unavailable(monkeypatch):
    class BrokenClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            raise RuntimeError("offline")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr("devdocs_rag.api.httpx.Client", BrokenClient)

    response = client.get("/models")

    assert response.status_code == 200
    payload = response.json()
    assert payload["available"] is False
    assert "llama3.1" in payload["fallback_models"]


def test_ask_accepts_frontend_schema(monkeypatch):
    chunk = Chunk(
        id="github_docs_1",
        text="Create a branch in your fork and open a pull request.",
        metadata={
            "source": "github_docs",
            "title": "About pull requests",
            "section": "Creating a pull request from a fork",
            "path": "content/pull-requests.md",
            "license": "CC-BY-4.0",
            "attribution": "GitHub Docs contributors",
        },
    )
    retrieved = RetrievedChunk(chunk=chunk, score=0.9, vector_score=0.7, keyword_score=0.8)

    class FakeRetriever:
        def search(self, query, top_k, source_filter, mode):
            assert query
            assert top_k == 3
            assert source_filter == ["github_docs"]
            assert mode == "hybrid"
            return [retrieved]

    class FakeGenerator:
        def answer(self, question, results, model=None):
            return Answer(
                question=question,
                text="Use a fork branch and open a pull request. [1]",
                sources=[
                    {
                        "source": "github_docs",
                        "title": "About pull requests",
                        "section": "Creating a pull request from a fork",
                        "path": "content/pull-requests.md",
                        "license": "CC-BY-4.0",
                        "attribution": "GitHub Docs contributors",
                        "score": "0.900",
                    }
                ],
                retrieved_chunks=results,
                latency_seconds=0.01,
                fallback_used=False,
            )

    monkeypatch.setattr(
        "devdocs_rag.api.load_retriever",
        lambda embedding_model=None: FakeRetriever(),
    )
    monkeypatch.setattr("devdocs_rag.api.load_generator", lambda: FakeGenerator())

    response = client.post(
        "/ask",
        json={
            "question": "How can I create a pull request from a fork?",
            "generation_model": "qwen2.5:7b",
            "embedding_model": "nomic-embed-text",
            "top_k": 3,
            "source_filter": ["github_docs"],
            "retrieval_mode": "hybrid",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["generation_model"] == "qwen2.5:7b"
    assert payload["retrieval_mode"] == "hybrid"
    assert payload["fallback_used"] is False
    assert payload["retrieved_chunks"][0]["metadata"]["source"] == "github_docs"
