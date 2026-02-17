"""Sync ServiceNow data and optional ingest to Pinecone."""

import os
from datetime import datetime
from typing import Any

import requests
from fastapi import HTTPException

from app.servicenow_extract import get_incidents, get_kb_knowledge
from app.services.clean_service import clean_incident, clean_kb
from app.services.rag_ingest_service import ingest_to_pinecone

_store: dict[str, Any] = {
    "incidents": [],
    "kb_knowledge": [],
    "synced_at": None,
}


def _get_session() -> requests.Session:
    session = requests.Session()
    session.headers.setdefault("Accept", "application/json")
    user = os.environ.get("SERVICENOW_USER")
    password = os.environ.get("SERVICENOW_PASSWORD")
    if user and password:
        session.auth = (user, password)
    return session


def sync_servicenow(ingest_to_vector: bool = True) -> dict[str, Any]:
    """Fetch from ServiceNow, store in memory, optionally run ingest_to_pinecone. Returns combined summary."""
    base_url = os.environ.get("SERVICENOW_INSTANCE", "").strip()
    if not base_url:
        raise HTTPException(
            status_code=503,
            detail="SERVICENOW_INSTANCE not set. Set env e.g. https://your-instance.service-now.com",
        )
    user = os.environ.get("SERVICENOW_USER")
    password = os.environ.get("SERVICENOW_PASSWORD")
    if not user or not password:
        raise HTTPException(
            status_code=503,
            detail="SERVICENOW_USER and SERVICENOW_PASSWORD must be set in .env for API access.",
        )
    session = _get_session()
    try:
        incidents = get_incidents(session, base_url)
        kb = get_kb_knowledge(session, base_url)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="ServiceNow 401. Check SERVICENOW_USER and SERVICENOW_PASSWORD and REST access.",
            )
        raise HTTPException(status_code=502, detail=f"ServiceNow request failed: {e!s}")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"ServiceNow request failed: {e!s}")

    _store["incidents"] = incidents
    _store["kb_knowledge"] = kb
    _store["synced_at"] = datetime.utcnow().isoformat() + "Z"

    out = {
        "status": "ok",
        "incidents_count": len(incidents),
        "kb_count": len(kb),
        "synced_at": _store["synced_at"],
    }

    if ingest_to_vector:
        ingest_result = ingest_to_pinecone(incidents, kb)
        out["ingest"] = ingest_result
    return out


def get_kb_data() -> dict[str, Any]:
    """Return last synced KB. Raises HTTPException if no data yet."""
    if not _store["kb_knowledge"] and _store["synced_at"] is None:
        raise HTTPException(status_code=404, detail="No data yet. Call POST /sync/servicenow first.")
    return {"count": len(_store["kb_knowledge"]), "data": _store["kb_knowledge"]}


def get_cleaned_text_by_sys_id(sys_id: str) -> str:
    """Return cleaned text for a record by sys_id from in-memory store. Used by RAG chat to build context."""
    for r in _store["incidents"]:
        if r.get("sys_id") == sys_id:
            text, _ = clean_incident(r)
            return text
    for r in _store["kb_knowledge"]:
        if r.get("sys_id") == sys_id:
            text, _ = clean_kb(r)
            return text
    return ""
