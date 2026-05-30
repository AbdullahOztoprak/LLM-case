from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from devdocs_rag.cli import ingest  # noqa: E402


def main(
    source: Annotated[str | None, typer.Option(help="Source name from sources.yaml.")] = None,
    sample_only: Annotated[
        bool,
        typer.Option(help="Index bundled sample docs instead of cloning sources."),
    ] = False,
    output: Annotated[Path, typer.Option()] = Path("data/generated/sample_index.json"),
) -> None:
    ingest(source=source, sample_only=sample_only, output=output)


if __name__ == "__main__":
    typer.run(main)
