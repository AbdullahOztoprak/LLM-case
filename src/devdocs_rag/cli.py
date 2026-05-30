from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .config import get_settings
from .embeddings import HashEmbeddingClient, OllamaEmbeddingClient
from .evaluation import evaluate_answers, evaluate_retrieval
from .generator import LocalGenerator
from .ingest import build_chunks, reset_generated_data
from .retriever import HybridRetriever
from .vector_store import JsonVectorStore

app = typer.Typer(help="Local developer docs RAG workbench.")


@app.command()
def ingest(
    source: Annotated[str | None, typer.Option(help="Source name from sources.yaml.")] = None,
    sample_only: Annotated[bool, typer.Option(help="Use bundled sample docs only.")] = False,
    output: Annotated[Path, typer.Option(help="JSON index path.")] = Path(
        "data/generated/sample_index.json"
    ),
) -> None:
    settings = get_settings()
    embedding_client = (
        OllamaEmbeddingClient(settings.ollama_base_url, settings.embedding_model)
        if settings.use_ollama_embeddings
        else HashEmbeddingClient()
    )
    chunks = build_chunks(
        source_name=source,
        sample_only=sample_only,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    reset_generated_data(output)
    store = JsonVectorStore(output, embedding_client)
    store.add(chunks)
    store.persist()
    mode = "sample docs" if sample_only else source or "all configured sources"
    typer.echo(f"Indexed {len(chunks)} chunks from {mode} into {output}.")


@app.command()
def ask(
    question: str,
    index: Annotated[Path, typer.Option(help="JSON index path.")] = Path(
        "data/generated/sample_index.json"
    ),
    top_k: Annotated[int, typer.Option(help="Number of chunks to retrieve.")] = 6,
) -> None:
    settings = get_settings()
    store = JsonVectorStore(index, HashEmbeddingClient())
    retriever = HybridRetriever(store)
    generator = LocalGenerator(settings.ollama_base_url, settings.generation_model)
    answer = generator.answer(question, retriever.search(question, top_k=top_k))
    typer.echo(answer.text)
    typer.echo("\nSources:")
    for source in answer.sources:
        typer.echo(f"- {source['source']} | {source['title']} | {source['section']}")


@app.command()
def eval(
    index: Annotated[Path, typer.Option(help="JSON index path.")] = Path(
        "data/generated/sample_index.json"
    ),
    eval_path: Annotated[Path, typer.Option(help="Eval JSONL path.")] = Path(
        "data/eval/eval_questions.jsonl"
    ),
) -> None:
    settings = get_settings()
    store = JsonVectorStore(index, HashEmbeddingClient())
    retriever = HybridRetriever(store)
    generator = LocalGenerator(settings.ollama_base_url, settings.generation_model)
    metrics = evaluate_retrieval(retriever, eval_path) | evaluate_answers(
        retriever,
        generator,
        eval_path,
    )
    typer.echo(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    app()
