"""RAG chat: search Pinecone, build context from in-memory store, answer with OpenAI."""

import os
from typing import Any

from fastapi import HTTPException

from app.services.embed_service import embed_texts
from app.services.pinecone_service import get_index, query_vectors
from app.services.sync_service import get_cleaned_text_by_sys_id

OPENAI_CHAT_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")


def answer_question(question: str, top_k: int = 10) -> dict[str, Any]:
    """Embed question, query Pinecone, build context from _store by sys_id, call OpenAI chat. Returns answer + sources."""
    question = (question or "").strip()
    top_k = min(max(1, top_k), 20)
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    try:
        query_vecs = embed_texts([question])
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    if not query_vecs:
        raise HTTPException(status_code=502, detail="Embed failed")
    query_vector = query_vecs[0]

    try:
        index = get_index()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    matches = query_vectors(index, query_vector, top_k=top_k)
    if not matches:
        return {
            "answer": "No relevant articles or incidents were found. Try rephrasing or run POST /sync/servicenow first.",
            "sources": [],
        }

    seen_sys_ids = set()
    context_parts = []
    sources = []
    for m in matches:
        meta = getattr(m, "metadata", None) if hasattr(m, "metadata") else (m.get("metadata") if isinstance(m, dict) else {})
        if not meta:
            continue
        sid = meta.get("sys_id", "") if isinstance(meta, dict) else getattr(meta, "sys_id", "")
        if not sid or sid in seen_sys_ids:
            continue
        seen_sys_ids.add(sid)
        text = get_cleaned_text_by_sys_id(sid)
        if not text:
            continue
        number = meta.get("number", "") if isinstance(meta, dict) else getattr(meta, "number", "")
        source = meta.get("source", "") if isinstance(meta, dict) else getattr(meta, "source", "")
        context_parts.append(f"[{source} {number}]\n{text}")
        sources.append({"sys_id": sid, "number": number, "source": source})

    if not context_parts:
        return {
            "answer": "Relevant records were found but no text is available in memory. Run POST /sync/servicenow first.",
            "sources": [],
        }

    context = "\n\n---\n\n".join(context_parts)
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY not set")
    from openai import OpenAI
    client = OpenAI(api_key=key)
    try:
        resp = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": "Answer the user's question using only the provided context from ServiceNow incidents and knowledge base. If the context does not contain the answer, say so. Do not make up information. Be concise."},
                {"role": "user", "content": f"Context:\n\n{context}\n\nQuestion: {question}"},
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI chat failed: {e!s}")
    choice = resp.choices[0] if resp.choices else None
    answer = choice.message.content if choice and choice.message else "No response."
    return {"answer": answer, "sources": sources}
