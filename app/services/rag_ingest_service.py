"""One shared ingest: clean -> chunk -> embed -> Pinecone. Used by manual sync and later auto-sync."""

from typing import Any

from fastapi import HTTPException

from app.services.clean_service import clean_all
from app.services.chunk_service import chunk_all
from app.services.embed_service import embed_texts
from app.services.pinecone_service import get_index, upsert_vectors


def ingest_to_pinecone(incidents: list[dict], kb_list: list[dict]) -> dict[str, Any]:
    """
    Clean, chunk, embed, and upsert incidents + KB into Pinecone.
    Returns summary dict. Raises HTTPException on config/API errors.
    """
    try:
        cleaned = clean_all(incidents, kb_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clean failed: {e!s}")

    if not cleaned:
        return {"status": "ok", "chunks_ingested": 0, "message": "No text to ingest"}

    try:
        chunks = chunk_all(cleaned)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk failed: {e!s}")

    if not chunks:
        return {"status": "ok", "chunks_ingested": 0, "message": "No chunks produced"}

    texts = [c[0] for c in chunks]
    metas = [c[1] for c in chunks]

    try:
        vectors = embed_texts(texts)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Embed failed: {e!s}")

    if len(vectors) != len(metas):
        raise HTTPException(status_code=500, detail="Embed count mismatch")

    try:
        index = get_index()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    try:
        count = upsert_vectors(index, vectors, metas)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Pinecone upsert failed: {e!s}")

    return {
        "status": "ok",
        "chunks_ingested": count,
        "records_cleaned": len(cleaned),
    }
