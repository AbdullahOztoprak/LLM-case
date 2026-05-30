from __future__ import annotations

import hashlib
import re
from pathlib import Path

from .models import Chunk, Document

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
RST_HEADING_RE = re.compile(r"^[=\-~^\"']{3,}\s*$")


def clean_markdown(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"\{%\s.*?%\}", "", text)
    text = re.sub(r"\{\{.*?\}\}", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def title_from_text(text: str, fallback: str) -> str:
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if match:
            return match.group(2).strip()
    return Path(fallback).stem.replace("-", " ").replace("_", " ").title()


def split_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown-ish text into titled sections."""

    sections: list[tuple[str, list[str]]] = []
    current_title = "Overview"
    current_lines: list[str] = []
    lines = text.splitlines()

    for index, line in enumerate(lines):
        heading = HEADING_RE.match(line.strip())
        rst_heading = index > 0 and RST_HEADING_RE.match(line.strip())
        if heading or rst_heading:
            if current_lines:
                sections.append((current_title, current_lines))
                current_lines = []
            current_title = heading.group(2).strip() if heading else lines[index - 1].strip()
            if not rst_heading:
                continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    parsed_sections = []
    for title, lines in sections:
        body = "\n".join(lines).strip()
        if body:
            parsed_sections.append((title, body))
    return parsed_sections


def sliding_windows(words: list[str], size: int, overlap: int) -> list[str]:
    if not words:
        return []
    if size <= overlap:
        raise ValueError("chunk_size must be larger than chunk_overlap")

    chunks = []
    step = size - overlap
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if window:
            chunks.append(" ".join(window))
        if start + size >= len(words):
            break
    return chunks


def stable_chunk_id(source: str, path: str, section: str, ordinal: int) -> str:
    raw = f"{source}:{path}:{section}:{ordinal}".encode()
    suffix = hashlib.sha1(raw).hexdigest()[:12]
    return f"{source}_{suffix}"


def chunk_document(document: Document, chunk_size: int = 700, overlap: int = 120) -> list[Chunk]:
    text = clean_markdown(document.text)
    path = document.metadata.get("path", "unknown")
    source = document.metadata.get("source", "unknown")
    title = document.metadata.get("title") or title_from_text(text, path)
    chunks: list[Chunk] = []

    for section, section_text in split_sections(text):
        words = section_text.split()
        for ordinal, chunk_text in enumerate(sliding_windows(words, chunk_size, overlap)):
            metadata = {
                **document.metadata,
                "title": title,
                "section": section,
                "chunk_ordinal": str(ordinal),
            }
            chunk_id = stable_chunk_id(source, path, section, ordinal)
            chunks.append(Chunk(id=chunk_id, text=chunk_text, metadata=metadata))

    return chunks
