from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    """A parsed source document before chunking."""

    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class Chunk:
    """A searchable chunk with source metadata."""

    id: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class RetrievedChunk:
    """A chunk returned by a retriever with a comparable score."""

    chunk: Chunk
    score: float
    vector_score: float = 0.0
    keyword_score: float = 0.0


@dataclass(frozen=True)
class Answer:
    """Answer text plus traceable retrieval context."""

    question: str
    text: str
    sources: list[dict[str, str]] = field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = field(default_factory=list)
    latency_seconds: float = 0.0
    fallback_used: bool = False
