from __future__ import annotations

import fnmatch
import shutil
import subprocess
from pathlib import Path
from typing import Any

import yaml

from .chunking import chunk_document, clean_markdown, title_from_text
from .models import Chunk, Document


def load_sources(path: Path = Path("sources.yaml")) -> list[dict[str, Any]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload.get("sources", [])


def clone_or_update_repo(repo: str, branch: str, target_dir: Path) -> Path:
    url = f"https://github.com/{repo}.git"
    if target_dir.exists():
        subprocess.run(
            ["git", "-C", str(target_dir), "fetch", "--depth", "1", "origin", branch],
            check=True,
        )
        subprocess.run(["git", "-C", str(target_dir), "checkout", branch], check=True)
        subprocess.run(
            ["git", "-C", str(target_dir), "pull", "--ff-only", "origin", branch],
            check=True,
        )
    else:
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", branch, url, str(target_dir)],
            check=True,
        )
    return target_dir


def matches_any(path: Path, patterns: list[str]) -> bool:
    normalized = path.as_posix()
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def documents_from_repo(source: dict[str, Any], raw_dir: Path = Path("data/raw")) -> list[Document]:
    repo = source["repo"]
    branch = source.get("branch", "main")
    repo_dir = raw_dir / source["name"]
    clone_or_update_repo(repo, branch, repo_dir)

    documents = []
    for path in repo_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".md", ".mdx", ".rst"}:
            continue
        relative = path.relative_to(repo_dir)
        if not matches_any(relative, source.get("include", ["**/*"])):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_markdown(text)
        documents.append(
            Document(
                text=cleaned,
                metadata={
                    "source": source["name"],
                    "path": relative.as_posix(),
                    "title": title_from_text(cleaned, relative.as_posix()),
                    "license": source.get("license", ""),
                    "attribution": source.get("attribution", ""),
                    "homepage": source.get("homepage", ""),
                },
            )
        )
    return documents


def sample_documents(sample_dir: Path = Path("data/sample")) -> list[Document]:
    documents = []
    for path in sorted(sample_dir.glob("*")):
        if path.suffix.lower() not in {".md", ".mdx", ".rst"}:
            continue
        source = path.stem.split("_sample")[0]
        text = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                text=text,
                metadata={
                    "source": source,
                    "path": path.as_posix(),
                    "title": title_from_text(text, path.name),
                    "license": "sample",
                    "attribution": "Sample documentation excerpt",
                    "homepage": "",
                },
            )
        )
    return documents


def build_chunks(
    sources: list[dict[str, Any]] | None = None,
    source_name: str | None = None,
    sample_only: bool = False,
    chunk_size: int = 700,
    chunk_overlap: int = 120,
) -> list[Chunk]:
    if sample_only:
        documents = sample_documents()
    else:
        selected_sources = sources or load_sources()
        if source_name:
            selected_sources = [
                source for source in selected_sources if source["name"] == source_name
            ]
            if not selected_sources:
                available = ", ".join(source["name"] for source in sources or load_sources())
                raise ValueError(f"Unknown source '{source_name}'. Available sources: {available}")
        documents = []
        for source in selected_sources:
            if source.get("type") in {"github_repo", "website_or_repo"} and source.get("repo"):
                documents.extend(documents_from_repo(source))
        if not documents:
            raise ValueError("No documents were found for the selected source manifest.")

    chunks: list[Chunk] = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size=chunk_size, overlap=chunk_overlap))
    return chunks


def reset_generated_data(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
