"""Clean raw ServiceNow text: strip HTML, merge fields, normalize."""

import re
from typing import Any

from bs4 import BeautifulSoup


def strip_html(html: str) -> str:
    if not html or not isinstance(html, str):
        return ""
    text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
    return text


def normalize(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_incident(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return (cleaned_text, metadata) for one incident."""
    parts = []
    title = record.get("short_description") or record.get("number") or ""
    if title:
        parts.append(f"Title: {strip_html(str(title))}")
    desc = record.get("description") or ""
    if desc:
        parts.append(f"Description: {strip_html(str(desc))}")
    work = record.get("work_notes") or ""
    if work:
        parts.append(f"Work notes: {strip_html(str(work))}")
    resolution = record.get("resolution_notes") or ""
    if resolution:
        parts.append(f"Resolution: {strip_html(str(resolution))}")
    cleaned = normalize(" ".join(parts)) if parts else ""
    metadata = {
        "sys_id": record.get("sys_id") or "",
        "number": record.get("number") or "",
        "source": "incident",
    }
    return cleaned, metadata


def clean_kb(record: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Return (cleaned_text, metadata) for one KB article."""
    parts = []
    title = record.get("short_description") or record.get("number") or ""
    if title:
        parts.append(f"Title: {strip_html(str(title))}")
    text = record.get("text") or ""
    if text:
        parts.append(strip_html(str(text)))
    cleaned = normalize(" ".join(parts)) if parts else ""
    metadata = {
        "sys_id": record.get("sys_id") or "",
        "number": record.get("number") or "",
        "source": "kb",
    }
    return cleaned, metadata


def clean_all(incidents: list[dict], kb_list: list[dict]) -> list[tuple[str, dict[str, Any]]]:
    """Return list of (cleaned_text, metadata) for all records (incidents then kb)."""
    out = []
    for r in incidents:
        text, meta = clean_incident(r)
        if text:
            out.append((text, meta))
    for r in kb_list:
        text, meta = clean_kb(r)
        if text:
            out.append((text, meta))
    return out
