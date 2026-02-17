"""FastAPI app. Swagger at /docs."""

import os

import app.config  # noqa: F401 - load .env
from fastapi import FastAPI

from app.routes.chat_routes import router as chat_router
from app.routes.sync_routes import router as sync_router

app = FastAPI(title="ServiceNow Data API", description="Sync and query ServiceNow incidents and KB.")

app.include_router(sync_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "6789"))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
