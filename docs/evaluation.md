# Evaluation

This project includes a compact evaluation loop so retrieval quality can be measured
instead of judged only by reading generated answers.

## Dataset

`data/eval/eval_questions.jsonl` stores one question per line:

```json
{"question": "How do I create a Python virtual environment?", "expected_source": "python_docs", "expected_keywords": ["venv", "python -m venv"]}
```

## Metrics

- `recall@3`: expected source appears in the top 3 retrieved chunks
- `recall@5`: expected source appears in the top 5 retrieved chunks
- `mrr`: mean reciprocal rank of the expected source
- `answer_citation_rate`: generated answers include source metadata
- `no_context_refusal_rate`: answer path refuses when context is insufficient
- latency: average retrieval and answer time

This is intentionally simple. It is enough to show whether changes to chunking,
embedding, source filters, or retrieval weights improve the system.
