from __future__ import annotations

from pathlib import Path

QUESTIONS = [
    {
        "question": "How can I create a pull request from a fork?",
        "expected_source": "github_docs",
        "expected_keywords": ["fork", "pull request", "branch"],
    },
    {
        "question": "How do I define path parameters in FastAPI?",
        "expected_source": "fastapi_docs",
        "expected_keywords": ["path parameter", "function parameter"],
    },
    {
        "question": "How do I create a Python virtual environment?",
        "expected_source": "python_docs",
        "expected_keywords": ["venv", "python -m venv"],
    },
    {
        "question": "How do I start services with Docker Compose?",
        "expected_source": "docker_docs",
        "expected_keywords": ["docker compose up", "services"],
    },
]


def main() -> None:
    import json

    output = Path("data/eval/eval_questions.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(json.dumps(question) for question in QUESTIONS) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(QUESTIONS)} questions to {output}.")


if __name__ == "__main__":
    main()
