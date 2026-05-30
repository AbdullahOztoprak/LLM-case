from __future__ import annotations

import json
import time
from pathlib import Path
from statistics import mean

from .generator import LocalGenerator
from .retriever import HybridRetriever


def load_eval_questions(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def evaluate_retrieval(
    retriever: HybridRetriever,
    eval_path: Path = Path("data/eval/eval_questions.jsonl"),
    top_values: tuple[int, ...] = (3, 5),
) -> dict[str, float]:
    questions = load_eval_questions(eval_path)
    metrics: dict[str, float] = {}
    reciprocal_ranks = []
    latencies = []

    for item in questions:
        question = str(item["question"])
        expected_source = str(item["expected_source"])
        started = time.perf_counter()
        results = retriever.search(question, top_k=max(top_values))
        latencies.append(time.perf_counter() - started)
        sources = [result.chunk.metadata.get("source") for result in results]
        for top_k in top_values:
            key = f"recall@{top_k}"
            metrics[key] = metrics.get(key, 0.0) + float(expected_source in sources[:top_k])
        rank = next(
            (
                index
                for index, source in enumerate(sources, start=1)
                if source == expected_source
            ),
            0,
        )
        reciprocal_ranks.append(1 / rank if rank else 0.0)

    total = max(len(questions), 1)
    for top_k in top_values:
        metrics[f"recall@{top_k}"] = metrics.get(f"recall@{top_k}", 0.0) / total
    metrics["mrr"] = mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    metrics["avg_retrieval_latency_seconds"] = mean(latencies) if latencies else 0.0
    return metrics


def evaluate_answers(
    retriever: HybridRetriever,
    generator: LocalGenerator,
    eval_path: Path = Path("data/eval/eval_questions.jsonl"),
    top_k: int = 5,
) -> dict[str, float]:
    questions = load_eval_questions(eval_path)
    citation_hits = 0
    refusal_hits = 0
    latencies = []
    for item in questions:
        results = retriever.search(str(item["question"]), top_k=top_k)
        answer = generator.answer(str(item["question"]), results)
        citation_hits += int(bool(answer.sources))
        refusal_hits += int("not enough" in answer.text.lower())
        latencies.append(answer.latency_seconds)
    total = max(len(questions), 1)
    return {
        "answer_citation_rate": citation_hits / total,
        "no_context_refusal_rate": refusal_hits / total,
        "avg_answer_latency_seconds": mean(latencies) if latencies else 0.0,
    }
