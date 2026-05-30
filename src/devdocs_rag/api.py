from __future__ import annotations

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import get_settings
from .pipeline import load_generator, load_retriever

app = FastAPI(title="Local Developer Docs RAG")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    generation_model: str | None = None
    embedding_model: str | None = None
    top_k: int | None = None
    source_filter: list[str] | None = None
    sources: list[str] | None = None
    retrieval_mode: str | None = Field(default=None, pattern="^(vector|bm25|hybrid)$")


def _model_name(model: dict[str, object]) -> str:
    name = model.get("name") or model.get("model")
    return str(name) if name else ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models")
def models():
    settings = get_settings()
    try:
        with httpx.Client(timeout=5) as client:
            response = client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        return {
            "available": False,
            "models": [],
            "fallback_models": [
                settings.generation_model or "llama3.1",
                settings.embedding_model or "nomic-embed-text",
            ],
            "message": f"Ollama is not reachable: {exc}",
        }

    model_names = [
        name for name in (_model_name(model) for model in payload.get("models", [])) if name
    ]
    return {
        "available": True,
        "models": model_names,
        "fallback_models": [],
        "message": "Loaded local Ollama models.",
    }


@app.post("/ask")
def ask(request: AskRequest):
    settings = get_settings()
    generation_model = request.generation_model or settings.generation_model or "llama3.1"
    embedding_model = request.embedding_model or settings.embedding_model or "nomic-embed-text"
    retrieval_mode = request.retrieval_mode or settings.retrieval_mode
    source_filter = request.source_filter if request.source_filter is not None else request.sources

    retriever = load_retriever(embedding_model=embedding_model)
    generator = load_generator()
    results = retriever.search(
        request.question,
        top_k=request.top_k or settings.top_k,
        source_filter=source_filter,
        mode=retrieval_mode,
    )
    answer = generator.answer(request.question, results, model=generation_model)
    return {
        "answer": answer.text,
        "sources": answer.sources,
        "retrieved_chunks": [
            {
                "id": result.chunk.id,
                "text": result.chunk.text,
                "combined_score": result.score,
                "score": result.score,
                "vector_score": result.vector_score,
                "bm25_score": result.keyword_score,
                "keyword_score": result.keyword_score,
                "metadata": result.chunk.metadata,
            }
            for result in answer.retrieved_chunks
        ],
        "latency_ms": round(answer.latency_seconds * 1000, 2),
        "generation_model": generation_model,
        "embedding_model": embedding_model,
        "retrieval_mode": retrieval_mode,
        "fallback_used": answer.fallback_used,
    }
