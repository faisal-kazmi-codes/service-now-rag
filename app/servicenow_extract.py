"""ServiceNow Table API: fetch incident and kb_knowledge data with pagination."""

from urllib.parse import urlparse

import requests


def _normalize_instance_url(url: str) -> str:
    """Use only scheme + netloc so path/query never get appended."""
    parsed = urlparse(url.strip())
    return f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else url.rstrip("/")


def _fetch_page(session, base_url, table, limit=1000, offset=0, query=None, fields=None):
    base = _normalize_instance_url(base_url)
    url = f"{base}/api/now/table/{table}"
    params = {"sysparm_limit": limit, "sysparm_offset": offset}
    if query:
        params["sysparm_query"] = query
    if fields:
        params["sysparm_fields"] = fields
    r = session.get(url, params=params)
    r.raise_for_status()
    return r.json().get("result", [])


def fetch_all(session, base_url, table, query=None, fields=None, limit=1000):
    out = []
    offset = 0
    while True:
        page = _fetch_page(
            session, base_url, table, limit=limit, offset=offset, query=query, fields=fields
        )
        out.extend(page)
        if len(page) < limit:
            break
        offset += limit
    return out


def get_incidents(session, base_url, query=None, fields=None):
    return fetch_all(session, base_url, "incident", query=query, fields=fields)


def get_kb_knowledge(session, base_url, query=None, fields=None):
    return fetch_all(session, base_url, "kb_knowledge", query=query, fields=fields)
