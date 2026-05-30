from devdocs_rag.chunking import chunk_document
from devdocs_rag.models import Document


def test_chunk_document_preserves_metadata_and_sections():
    document = Document(
        text="# Main Title\n\nIntro text.\n\n## Install\n\nRun the installer.",
        metadata={"source": "docs", "path": "install.md", "license": "MIT"},
    )

    chunks = chunk_document(document, chunk_size=10, overlap=2)

    assert chunks
    assert chunks[0].metadata["source"] == "docs"
    assert chunks[0].metadata["title"] == "Main Title"
    assert {chunk.metadata["section"] for chunk in chunks} >= {"Main Title", "Install"}


def test_chunk_size_must_be_larger_than_overlap():
    document = Document(text="# Title\n\nSome text", metadata={"source": "docs", "path": "x.md"})

    try:
        chunk_document(document, chunk_size=5, overlap=5)
    except ValueError as exc:
        assert "chunk_size" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
