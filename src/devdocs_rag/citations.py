from __future__ import annotations

from .models import RetrievedChunk


def source_key(result: RetrievedChunk) -> tuple[str, str, str]:
    metadata = result.chunk.metadata
    return (
        metadata.get("source", "unknown"),
        metadata.get("title", "Untitled"),
        metadata.get("path", ""),
    )


def build_sources(results: list[RetrievedChunk]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    sources = []
    for result in results:
        key = source_key(result)
        if key in seen:
            continue
        seen.add(key)
        metadata = result.chunk.metadata
        sources.append(
            {
                "source": metadata.get("source", "unknown"),
                "title": metadata.get("title", "Untitled"),
                "section": metadata.get("section", "Overview"),
                "path": metadata.get("path", ""),
                "license": metadata.get("license", ""),
                "attribution": metadata.get("attribution", ""),
                "score": f"{result.score:.3f}",
            }
        )
    return sources


def format_sources(sources: list[dict[str, str]]) -> str:
    lines = []
    for index, source in enumerate(sources, start=1):
        label = f"{source['source']} - {source['title']}"
        detail = source.get("section") or source.get("path")
        lines.append(f"[{index}] {label} ({detail})")
    return "\n".join(lines)
