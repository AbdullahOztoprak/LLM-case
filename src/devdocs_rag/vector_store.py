from __future__ import annotations

import json
from pathlib import Path

from .embeddings import EmbeddingClient, cosine_similarity
from .models import Chunk, RetrievedChunk


class JsonVectorStore:
    """Small persistent vector store for local sample runs and CI."""

    def __init__(self, path: Path, embedding_client: EmbeddingClient) -> None:
        self.path = path
        self.embedding_client = embedding_client
        self._chunks: list[Chunk] = []
        self._embeddings: list[list[float]] = []
        if path.exists():
            self.load()

    @property
    def chunks(self) -> list[Chunk]:
        return self._chunks

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        self._chunks.extend(chunks)
        self._embeddings.extend(self.embedding_client.embed([chunk.text for chunk in chunks]))

    def persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata, "embedding": embedding}
            for chunk, embedding in zip(self._chunks, self._embeddings, strict=True)
        ]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load(self) -> None:
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        self._chunks = [
            Chunk(id=item["id"], text=item["text"], metadata=item["metadata"]) for item in payload
        ]
        self._embeddings = [item["embedding"] for item in payload]

    def search(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        query_embedding = self.embedding_client.embed([query])[0]
        scored = [
            RetrievedChunk(
                chunk=chunk,
                score=cosine_similarity(query_embedding, embedding),
                vector_score=cosine_similarity(query_embedding, embedding),
            )
            for chunk, embedding in zip(self._chunks, self._embeddings, strict=True)
        ]
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


class ChromaVectorStore:
    """Chroma-backed persistent vector store for larger local indexes."""

    def __init__(
        self,
        persist_directory: Path,
        embedding_client: EmbeddingClient,
        collection_name: str = "devdocs",
    ) -> None:
        import chromadb

        self.embedding_client = embedding_client
        self.client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        embeddings = self.embedding_client.embed([chunk.text for chunk in chunks])
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )

    def search(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        query_embedding = self.embedding_client.embed([query])[0]
        result = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
        chunks = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0] or [0.0] * len(ids)
        rows = zip(ids, documents, metadatas, distances, strict=False)
        for chunk_id, text, metadata, distance in rows:
            score = 1.0 / (1.0 + float(distance))
            chunks.append(RetrievedChunk(Chunk(chunk_id, text, metadata or {}), score=score))
        return chunks
