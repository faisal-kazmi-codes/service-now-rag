"""Pinecone index connection and upsert."""

import os
from typing import Any

from pinecone import Pinecone

INDEX_NAME_ENV = "PINECONE_INDEX_NAME"


def get_client() -> Pinecone:
    key = os.environ.get("PINECONE_API_KEY")
    if not key:
        raise ValueError("PINECONE_API_KEY not set")
    return Pinecone(api_key=key)


def get_index():
    name = os.environ.get(INDEX_NAME_ENV)
    if not name:
        raise ValueError(f"{INDEX_NAME_ENV} not set")
    return get_client().Index(name)


def chunk_id(meta: dict[str, Any]) -> str:
    """Stable id for upsert and later replace-by-record."""
    src = meta.get("source", "")
    sid = meta.get("sys_id", "")
    idx = meta.get("chunk_index", 0)
    return f"{src}_{sid}_{idx}"


def upsert_vectors(
    index,
    vectors: list[list[float]],
    chunks_metadata: list[dict[str, Any]],
    batch_size: int = 100,
) -> int:
    """Upsert (id, vector, metadata) in batches. Metadata values must be str/int/float/bool/list. Returns count upserted."""
    # Pinecone metadata allows only str, int, float, bool, list of those
    def sanitize(m: dict) -> dict:
        out = {}
        for k, v in m.items():
            if v is None:
                continue
            if isinstance(v, (str, int, float, bool)):
                out[k] = v
            elif isinstance(v, list):
                out[k] = [x for x in v if isinstance(x, (str, int, float, bool))][:100]
            else:
                out[k] = str(v)
        return out

    total = 0
    for i in range(0, len(vectors), batch_size):
        batch_vecs = vectors[i : i + batch_size]
        batch_meta = chunks_metadata[i : i + batch_size]
        ups = [
            {"id": chunk_id(m), "values": vec, "metadata": sanitize(m)}
            for vec, m in zip(batch_vecs, batch_meta)
        ]
        index.upsert(vectors=ups)
        total += len(ups)
    return total


def query_vectors(index, vector: list[float], top_k: int = 10):
    """Query index by vector. Returns list of matches with id, score, metadata."""
    res = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return list(getattr(res, "matches", []) or [])
