#!/usr/bin/env python3
"""Fetch ServiceNow incident and kb_knowledge data. Writes incidents.json and kb_knowledge.json."""

import json
import os
import sys

import requests

import app.config  # noqa: F401 - load .env
from app.servicenow_extract import get_incidents, get_kb_knowledge


def main():
    base_url = os.environ.get("SERVICENOW_INSTANCE", "").rstrip("/")
    if not base_url:
        print("Set SERVICENOW_INSTANCE (e.g. https://your-instance.service-now.com)", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.setdefault("Accept", "application/json")
    user = os.environ.get("SERVICENOW_USER")
    password = os.environ.get("SERVICENOW_PASSWORD")
    if user and password:
        session.auth = (user, password)

    print("Fetching incidents...")
    incidents = get_incidents(session, base_url)
    print(f"  Got {len(incidents)} incidents")

    print("Fetching kb_knowledge...")
    kb = get_kb_knowledge(session, base_url)
    print(f"  Got {len(kb)} KB articles")

    with open("incidents.json", "w") as f:
        json.dump(incidents, f, indent=2)
    with open("kb_knowledge.json", "w") as f:
        json.dump(kb, f, indent=2)

    print("Wrote incidents.json and kb_knowledge.json")


if __name__ == "__main__":
    main()
