from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from devdocs_rag.cli import eval as run_eval  # noqa: E402


def main(
    index: Annotated[Path, typer.Option()] = Path("data/generated/sample_index.json"),
    eval_path: Annotated[Path, typer.Option()] = Path("data/eval/eval_questions.jsonl"),
) -> None:
    run_eval(index=index, eval_path=eval_path)


if __name__ == "__main__":
    typer.run(main)
