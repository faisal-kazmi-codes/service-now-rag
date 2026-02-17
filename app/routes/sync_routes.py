"""Routes: sync and data/kb."""

from fastapi import APIRouter

from app.services.sync_service import get_kb_data, sync_servicenow

router = APIRouter()


@router.post("/sync/servicenow")
def sync_servicenow_route():
    """Fetch from ServiceNow and ingest into Pinecone (clean -> chunk -> embed -> upsert)."""
    return sync_servicenow(ingest_to_vector=True)


@router.get("/data/kb")
def get_data_kb_route():
    """Return last synced KB articles. Sync first via POST /sync/servicenow."""
    return get_kb_data()
