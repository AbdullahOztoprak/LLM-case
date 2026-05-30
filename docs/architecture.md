# Architecture

The system is a local RAG pipeline for developer documentation.

1. `sources.yaml` describes official documentation sources, include patterns, licenses,
   and attribution text.
2. `devdocs_rag.ingest` clones or reads sources and converts markdown-like files into
   `Document` objects.
3. `devdocs_rag.chunking` cleans docs, detects headings, and creates stable chunks with
   metadata.
4. `devdocs_rag.embeddings` generates vectors. Ollama can be used for `nomic-embed-text`;
   tests use deterministic hash embeddings.
5. `devdocs_rag.retriever` combines vector search and BM25 keyword search.
6. `devdocs_rag.generator` sends retrieved context to a local Ollama model and formats
   fallback retrieval previews when Ollama is unavailable.
7. `devdocs_rag.api` exposes `/ask`, `/models`, and `/health` for the React dashboard.
8. `frontend/` provides the main React/Vite workbench UI with model selection, source
   filters, retrieval mode controls, citations, and chunk scores.
9. `devdocs_rag.evaluation` measures retrieval and answer behavior on a small JSONL
   dataset.

The design keeps the pipeline inspectable. The UI shows sources, chunk scores, vector
score, keyword score, and latency.
