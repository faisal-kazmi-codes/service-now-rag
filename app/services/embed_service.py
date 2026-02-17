"""OpenAI embeddings in batches."""

import os

from openai import OpenAI

EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
EMBED_DIMENSIONS = int(os.environ.get("EMBED_DIMENSIONS", "512"))
BATCH_SIZE = int(os.environ.get("EMBED_BATCH_SIZE", "100"))


def get_client() -> OpenAI:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not set")
    return OpenAI(api_key=key)


def embed_texts(texts, model=None, dimensions=None):
    """Embed a list of texts. Returns list of vectors."""
    if not texts:
        return []
    model = model or EMBED_MODEL
    dimensions = dimensions if dimensions is not None else EMBED_DIMENSIONS
    client = get_client()   
    out = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(input=batch, model=model, dimensions=dimensions)
        by_idx = {e.index: e.embedding for e in resp.data}
        out.extend([by_idx[j] for j in range(len(batch))])
    return out
