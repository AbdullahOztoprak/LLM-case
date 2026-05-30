from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from .models import Chunk, RetrievedChunk
from .vector_store import JsonVectorStore

TOKEN_RE = re.compile(r"[a-zA-Z0-9_./-]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize(chunk.text) for chunk in chunks]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / max(len(self.doc_lengths), 1)
        self.term_frequencies = [Counter(tokens) for tokens in self.doc_tokens]
        self.doc_frequency: dict[str, int] = defaultdict(int)
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.doc_frequency[token] += 1

    def score(self, query: str) -> list[float]:
        query_terms = tokenize(query)
        total_docs = max(len(self.chunks), 1)
        scores = []
        for index, frequencies in enumerate(self.term_frequencies):
            score = 0.0
            doc_length = self.doc_lengths[index] or 1
            for term in query_terms:
                if term not in frequencies:
                    continue
                idf = math.log(
                    1
                    + (total_docs - self.doc_frequency[term] + 0.5)
                    / (self.doc_frequency[term] + 0.5)
                )
                numerator = frequencies[term] * (self.k1 + 1)
                denominator = frequencies[term] + self.k1 * (
                    1 - self.b + self.b * doc_length / max(self.avg_doc_length, 1)
                )
                score += idf * numerator / denominator
            scores.append(score)
        return scores

    def search(self, query: str, top_k: int) -> list[RetrievedChunk]:
        scores = self.score(query)
        ranked = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        return [
            RetrievedChunk(chunk=self.chunks[index], score=score, keyword_score=score)
            for index, score in ranked[:top_k]
            if score > 0
        ]


class HybridRetriever:
    def __init__(
        self,
        vector_store: JsonVectorStore,
        vector_weight: float = 0.65,
        keyword_weight: float = 0.35,
    ) -> None:
        self.vector_store = vector_store
        self.bm25 = BM25Index(vector_store.chunks)
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

    def search(
        self,
        query: str,
        top_k: int = 6,
        source_filter: list[str] | None = None,
        mode: str = "hybrid",
    ) -> list[RetrievedChunk]:
        mode = mode.lower()
        if mode == "vector":
            return [
                result
                for result in self.vector_store.search(query, top_k=max(top_k * 4, 12))
                if not source_filter or result.chunk.metadata.get("source") in source_filter
            ][:top_k]

        if mode == "bm25":
            return [
                result
                for result in self.bm25.search(query, top_k=max(top_k * 4, 12))
                if not source_filter or result.chunk.metadata.get("source") in source_filter
            ][:top_k]

        if mode != "hybrid":
            raise ValueError("retrieval mode must be one of: vector, bm25, hybrid")

        vector_results = self.vector_store.search(query, top_k=max(top_k * 4, 12))
        keyword_results = self.bm25.search(query, top_k=max(top_k * 4, 12))
        max_vector = max([result.score for result in vector_results] or [1.0])
        max_keyword = max([result.score for result in keyword_results] or [1.0])

        combined: dict[str, dict[str, float | Chunk]] = {}
        for result in vector_results:
            combined[result.chunk.id] = {
                "chunk": result.chunk,
                "vector": result.score / max_vector if max_vector else 0.0,
                "keyword": 0.0,
            }
        for result in keyword_results:
            item = combined.setdefault(
                result.chunk.id,
                {"chunk": result.chunk, "vector": 0.0, "keyword": 0.0},
            )
            item["keyword"] = result.score / max_keyword if max_keyword else 0.0

        ranked = []
        for item in combined.values():
            chunk = item["chunk"]
            if not isinstance(chunk, Chunk):
                continue
            if source_filter and chunk.metadata.get("source") not in source_filter:
                continue
            vector_score = float(item["vector"])
            keyword_score = float(item["keyword"])
            score = self.vector_weight * vector_score + self.keyword_weight * keyword_score
            ranked.append(
                RetrievedChunk(
                    chunk=chunk,
                    score=score,
                    vector_score=vector_score,
                    keyword_score=keyword_score,
                )
            )
        return sorted(ranked, key=lambda result: result.score, reverse=True)[:top_k]
