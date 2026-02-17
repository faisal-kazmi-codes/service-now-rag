"""Chunk long text by token count with overlap. Uses tiktoken (OpenAI)."""

import os
from typing import Any

import tiktoken

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "80"))
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")


def get_encoding(model: str | None = None):
    m = model or EMBED_MODEL
    try:
        return tiktoken.encoding_for_model(m)
    except KeyError:
        return tiktoken.get_encoding("cl100k_base")


def chunk_text(
    text: str,
    metadata: dict[str, Any],
    chunk_size: int | None = None,
    overlap: int | None = None,
    encoding=None,
) -> list[tuple[str, dict[str, Any]]]:
    """Split text into chunks by token count with overlap. Returns [(chunk_text, metadata), ...]."""
    chunk_size = chunk_size if chunk_size is not None else CHUNK_SIZE
    overlap = overlap if overlap is not None else CHUNK_OVERLAP
    if encoding is None:
        encoding = get_encoding()
    tokens = encoding.encode(text)
    if len(tokens) <= chunk_size:
        return [(text, {**metadata, "chunk_index": 0})] if text.strip() else []

    step = chunk_size - overlap
    out = []
    start = 0
    idx = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = encoding.decode(chunk_tokens)
        meta = {**metadata, "chunk_index": idx}
        out.append((chunk_text_str, meta))
        idx += 1
        if end >= len(tokens):
            break
        start = start + step
    return out


def chunk_all(
    items: list[tuple[str, dict[str, Any]]],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """Chunk a list of (text, metadata). Returns flat list of (chunk_text, metadata)."""
    chunk_size = chunk_size if chunk_size is not None else CHUNK_SIZE
    overlap = overlap if overlap is not None else CHUNK_OVERLAP
    enc = get_encoding()
    result = []
    for text, meta in items:
        result.extend(chunk_text(text, meta, chunk_size=chunk_size, overlap=overlap, encoding=enc))
    return result
