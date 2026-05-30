from devdocs_rag.citations import build_sources, format_sources
from devdocs_rag.models import Chunk, RetrievedChunk


def test_build_sources_deduplicates_by_document():
    chunk = Chunk(
        id="a",
        text="Example",
        metadata={
            "source": "github_docs",
            "title": "Pull requests",
            "section": "Overview",
            "path": "pulls.md",
            "license": "CC-BY-4.0",
            "attribution": "GitHub Docs contributors",
        },
    )

    sources = build_sources([RetrievedChunk(chunk, 0.9), RetrievedChunk(chunk, 0.8)])

    assert len(sources) == 1
    assert sources[0]["source"] == "github_docs"
    assert "[1]" in format_sources(sources)
