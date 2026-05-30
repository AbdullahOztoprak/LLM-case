from __future__ import annotations

import time

import httpx

from .citations import build_sources, format_sources
from .models import Answer, RetrievedChunk

SYSTEM_PROMPT = """Answer developer documentation questions using only the retrieved
context. If the context is not enough, say that the documentation context is not enough
to answer confidently. Keep answers practical and cite sources using [1], [2] style
references."""


def build_prompt(question: str, results: list[RetrievedChunk]) -> str:
    context_blocks = []
    sources = build_sources(results)
    source_numbers = {
        (source["source"], source["title"], source["path"]): index
        for index, source in enumerate(sources, start=1)
    }
    for result in results:
        metadata = result.chunk.metadata
        key = (metadata.get("source", ""), metadata.get("title", ""), metadata.get("path", ""))
        source_number = source_numbers.get(key, 1)
        context_blocks.append(
            f"[{source_number}] {metadata.get('title', 'Untitled')} / "
            f"{metadata.get('section', 'Overview')}\n{result.chunk.text}"
        )

    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved context:\n\n" + "\n\n---\n\n".join(context_blocks) + "\n\nAnswer:"
    )


class LocalGenerator:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def answer(
        self,
        question: str,
        results: list[RetrievedChunk],
        model: str | None = None,
    ) -> Answer:
        start = time.perf_counter()
        sources = build_sources(results)
        selected_model = model or self.model
        if not results:
            return Answer(
                question=question,
                text="I do not have enough retrieved documentation context to answer confidently.",
                sources=[],
                retrieved_chunks=[],
                latency_seconds=time.perf_counter() - start,
                fallback_used=True,
            )

        prompt = build_prompt(question, results)
        try:
            with httpx.Client(timeout=120) as client:
                response = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": selected_model, "prompt": prompt, "stream": False},
                )
                response.raise_for_status()
                text = response.json().get("response", "").strip()
                fallback_used = False
        except Exception:
            text = fallback_answer(question, results, sources)
            fallback_used = True

        return Answer(
            question=question,
            text=text,
            sources=sources,
            retrieved_chunks=results,
            latency_seconds=time.perf_counter() - start,
            fallback_used=fallback_used,
        )


def fallback_answer(
    question: str,
    results: list[RetrievedChunk],
    sources: list[dict[str, str]],
) -> str:
    best = results[0]
    excerpt = best.chunk.text
    if len(excerpt) > 700:
        excerpt = excerpt[:697].rsplit(" ", 1)[0] + "..."
    source_block = format_sources(sources[:3])
    return (
        "Ollama is not reachable, so this is a retrieval-only preview.\n\n"
        f"Most relevant context for: {question}\n\n"
        f"{excerpt}\n\nSources:\n{source_block}"
    )
